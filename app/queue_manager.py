"""
SQLite-backed verification queue for single-image async processing.

Design goals:
- One SQLite DB file shared between the API container and the worker container
  via a bind-mounted Docker volume (/app/tmp).
- WAL mode so readers never block the writer and vice-versa.
- The worker always processes one job at a time (no concurrency on the GPU side).
- The API container only reads (status queries) and writes (enqueue new jobs).
- Retries: each job may be attempted up to MAX_ATTEMPTS times before being
  permanently marked FAILED.

Table: verify_jobs
  id            TEXT PRIMARY KEY  (UUID4)
  status        TEXT              pending | processing | completed | failed | cancelled
  attempts      INTEGER           number of processing attempts so far
  max_attempts  INTEGER           max allowed attempts (default 3)
  image_path    TEXT              path to saved image inside shared volume
  ground_truth  TEXT              JSON string, nullable
  result        TEXT              JSON string of VerifyResponse-compatible dict, nullable
  error         TEXT              last error message, nullable
  created_at    REAL              Unix timestamp (float)
  updated_at    REAL              Unix timestamp (float)
  completed_at  REAL              Unix timestamp, nullable
"""

import json
import logging
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger("ttb_queue")

# Shared DB file lives on the bind-mounted volume so both containers see it.
_DEFAULT_DB_PATH = Path("/app/tmp/queue.db")

# How long after completion before a record is eligible for cleanup (seconds).
_COMPLETED_RETENTION_SECONDS = 4 * 3600  # 4 hours


class QueueManager:
    """Thread-safe, multi-process-safe SQLite queue for verify jobs."""

    def __init__(self, db_path: Path = _DEFAULT_DB_PATH, max_attempts: int = 3):
        self.db_path = db_path
        self.max_attempts = max_attempts
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """
        Open a connection with WAL mode and a short busy timeout so concurrent
        writers back off gracefully instead of raising OperationalError.
        """
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _db(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create table if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verify_jobs (
                    id            TEXT    PRIMARY KEY,
                    status        TEXT    NOT NULL DEFAULT 'pending',
                    attempts      INTEGER NOT NULL DEFAULT 0,
                    max_attempts  INTEGER NOT NULL DEFAULT 3,
                    image_path    TEXT    NOT NULL,
                    ground_truth  TEXT,
                    result        TEXT,
                    error         TEXT,
                    created_at    REAL    NOT NULL,
                    updated_at    REAL    NOT NULL,
                    completed_at  REAL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON verify_jobs (status)"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(
        self,
        image_path: str,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a new job to the queue.

        Args:
            image_path: Absolute path to the image file (on shared volume).
            ground_truth: Optional dict of expected label fields.

        Returns:
            job_id (UUID4 string)
        """
        job_id = str(uuid.uuid4())
        now = time.time()
        ground_truth_json = json.dumps(ground_truth) if ground_truth else None

        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO verify_jobs
                    (id, status, attempts, max_attempts, image_path,
                     ground_truth, result, error, created_at, updated_at)
                VALUES (?, 'pending', 0, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (job_id, self.max_attempts, image_path, ground_truth_json, now, now),
            )

        logger.info(f"[queue] Enqueued job {job_id} for {Path(image_path).name}")
        return job_id

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Atomically claim the next pending job for processing.

        Returns a dict with the job's fields, or None if the queue is empty.
        Uses a write transaction with a SELECT … WHERE status='pending' ORDER BY
        created_at LIMIT 1, then immediately updates to 'processing'.
        """
        with self._db() as conn:
            row = conn.execute(
                """
                SELECT * FROM verify_jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            now = time.time()
            conn.execute(
                """
                UPDATE verify_jobs
                SET status = 'processing',
                    attempts = attempts + 1,
                    updated_at = ?
                WHERE id = ?
                """,
                (now, row["id"]),
            )

        job = dict(row)
        job["attempts"] += 1  # reflect the increment above
        job["status"] = "processing"  # reflect the UPDATE above
        if job.get("ground_truth"):
            job["ground_truth"] = json.loads(job["ground_truth"])
        return job

    def complete(self, job_id: str, result: Dict[str, Any]) -> None:
        """Mark a job as successfully completed with its result dict."""
        now = time.time()
        with self._db() as conn:
            conn.execute(
                """
                UPDATE verify_jobs
                SET status = 'completed',
                    result = ?,
                    error = NULL,
                    updated_at = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (json.dumps(result), now, now, job_id),
            )
        logger.info(f"[queue] Job {job_id} completed")

    def fail(self, job_id: str, error: str) -> None:
        """
        Record a processing failure for a job.

        If the job has remaining attempts, put it back to 'pending' so the
        worker will retry.  If all attempts are exhausted, mark 'failed'.
        """
        now = time.time()
        with self._db() as conn:
            row = conn.execute(
                "SELECT attempts, max_attempts FROM verify_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()

            if row is None:
                logger.warning(f"[queue] fail() called for unknown job {job_id}")
                return

            if row["attempts"] < row["max_attempts"]:
                # Still have retries left — requeue
                conn.execute(
                    """
                    UPDATE verify_jobs
                    SET status = 'pending',
                        error = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (error, now, job_id),
                )
                logger.warning(
                    f"[queue] Job {job_id} failed (attempt {row['attempts']}"
                    f"/{row['max_attempts']}), requeuing. Error: {error}"
                )
            else:
                # All retries exhausted
                conn.execute(
                    """
                    UPDATE verify_jobs
                    SET status = 'failed',
                        error = ?,
                        updated_at = ?,
                        completed_at = ?
                    WHERE id = ?
                    """,
                    (error, now, now, job_id),
                )
                logger.error(
                    f"[queue] Job {job_id} permanently failed after "
                    f"{row['attempts']} attempts. Error: {error}"
                )

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID.  Returns None if not found."""
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM verify_jobs WHERE id = ?", (job_id,)
            ).fetchone()

        if row is None:
            return None

        job = dict(row)
        if job.get("ground_truth"):
            job["ground_truth"] = json.loads(job["ground_truth"])
        if job.get("result"):
            job["result"] = json.loads(job["result"])
        return job

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a pending job.  Has no effect if the job is already
        processing/completed/failed.

        Returns True if the job was actually cancelled.
        """
        now = time.time()
        with self._db() as conn:
            cursor = conn.execute(
                """
                UPDATE verify_jobs
                SET status = 'cancelled', updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (now, job_id),
            )
        cancelled = cursor.rowcount > 0
        if cancelled:
            logger.info(f"[queue] Job {job_id} cancelled")
        return cancelled

    def cleanup_old_jobs(self, retention_seconds: int = _COMPLETED_RETENTION_SECONDS) -> int:
        """
        Delete terminal jobs (completed/failed/cancelled) older than
        retention_seconds.  Returns the number of rows deleted.
        """
        cutoff = time.time() - retention_seconds
        with self._db() as conn:
            cursor = conn.execute(
                """
                DELETE FROM verify_jobs
                WHERE status IN ('completed', 'failed', 'cancelled')
                  AND updated_at < ?
                """,
                (cutoff,),
            )
        count = cursor.rowcount
        if count:
            logger.info(f"[queue] Cleaned up {count} old verify jobs")
        return count

    def queue_depth(self) -> int:
        """Return the number of jobs currently in 'pending' status."""
        with self._db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as n FROM verify_jobs WHERE status = 'pending'"
            ).fetchone()
        return row["n"] if row else 0

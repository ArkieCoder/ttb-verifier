"""
TTB Label Verifier — queue worker process.

Runs as a separate Docker container.  Polls the SQLite queue for pending
verify jobs, processes them one at a time through Ollama, and writes results
back to the queue.  Never holds more than one Ollama request in flight, which
eliminates all GPU-level concurrency issues.

Usage (inside container):
    python worker.py

Environment variables (same as the main app):
    OLLAMA_HOST              default: http://ollama:11434
    OLLAMA_MODEL             default: llama3.2-vision
    OLLAMA_TIMEOUT_SECONDS   default: 12   (short — we retry on timeout)
    WORKER_POLL_INTERVAL     default: 2    (seconds between empty-queue polls)
    LOG_LEVEL                default: INFO
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ttb_worker")


# ---------------------------------------------------------------------------
# Configuration (no pydantic dependency — plain env vars)
# ---------------------------------------------------------------------------

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
# Short per-attempt timeout: inference normally takes ~10s, so 12s gives a
# small cushion while still failing fast enough to retry within the overall
# CloudFront window (60s) if the job is retried on the NEXT request.
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "12"))
POLL_INTERVAL = float(os.getenv("WORKER_POLL_INTERVAL", "2"))

# Shared volume path — must match the API container.
DB_PATH = Path(os.getenv("QUEUE_DB_PATH", "/app/tmp/queue.db"))


# ---------------------------------------------------------------------------
# Queue manager (imported after setting DB_PATH)
# ---------------------------------------------------------------------------

# Add /app to sys.path so we can import local modules.
sys.path.insert(0, "/app")

from queue_manager import QueueManager  # noqa: E402
from label_validator import LabelValidator  # noqa: E402


# ---------------------------------------------------------------------------
# Worker loop
# ---------------------------------------------------------------------------


def process_job(job: dict, validator: LabelValidator) -> dict:
    """
    Run label validation for a single queued job.

    Args:
        job: Row dict from QueueManager.dequeue()
        validator: Reused LabelValidator instance (keeps Ollama model in GPU)

    Returns:
        result dict compatible with VerifyResponse
    """
    image_path = job["image_path"]
    ground_truth = job.get("ground_truth")  # already decoded to dict by QueueManager

    logger.info(
        f"[worker] Processing job {job['id']} "
        f"(attempt {job['attempts']}/{job['max_attempts']}): "
        f"{Path(image_path).name}"
    )

    result = validator.validate_label(image_path, ground_truth)
    result["image_path"] = Path(image_path).name
    return result


def run_worker() -> None:
    """Main worker loop — runs indefinitely until killed."""
    logger.info(
        f"[worker] Starting. "
        f"Ollama: {OLLAMA_HOST}, model: {OLLAMA_MODEL}, "
        f"timeout: {OLLAMA_TIMEOUT}s, poll: {POLL_INTERVAL}s"
    )

    queue = QueueManager(db_path=DB_PATH)

    # We create a single LabelValidator (and therefore a single Ollama client)
    # and reuse it across jobs.  This keeps the model in GPU memory (keep_alive=-1)
    # and avoids connection churn.
    validator = None

    while True:
        try:
            job = queue.dequeue()
        except Exception as exc:
            logger.error(f"[worker] Failed to dequeue: {exc}", exc_info=True)
            time.sleep(POLL_INTERVAL)
            continue

        if job is None:
            # Queue is empty — sleep and poll again
            time.sleep(POLL_INTERVAL)
            continue

        job_id = job["id"]

        # Lazy-init validator (avoids crashing at startup if Ollama isn't ready yet)
        if validator is None:
            try:
                validator = LabelValidator(
                    ollama_host=OLLAMA_HOST,
                    timeout=OLLAMA_TIMEOUT,
                )
                logger.info("[worker] LabelValidator initialised")
            except Exception as exc:
                err = f"Failed to initialise LabelValidator: {exc}"
                logger.error(f"[worker] {err}", exc_info=True)
                queue.fail(job_id, err)
                time.sleep(POLL_INTERVAL)
                continue

        try:
            result = process_job(job, validator)
            queue.complete(job_id, result)

        except Exception as exc:
            err = str(exc)
            logger.error(
                f"[worker] Job {job_id} failed: {err}",
                exc_info=True,
            )
            # If it looks like a connection/timeout error, discard the validator
            # so we rebuild the Ollama client on the next job.
            err_lower = err.lower()
            if any(
                kw in err_lower
                for kw in ("timeout", "connect", "connection", "read error", "eof")
            ):
                logger.warning(
                    "[worker] Discarding validator due to connection error — "
                    "will reinitialise for next job"
                )
                validator = None

            queue.fail(job_id, err)


if __name__ == "__main__":
    run_worker()

"""
Job manager for asynchronous batch processing.

Handles job state persistence using file-based storage with fcntl locking
to support multiple uvicorn workers accessing the same job files.
"""

import fcntl
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.logger import get_logger

logger = get_logger(__name__)

# Job storage directory
JOBS_DIR = Path("/app/tmp/jobs")


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """Represents a batch processing job."""
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    total_images: int
    processed_images: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        # Convert enum to string
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        """Create job from dictionary loaded from JSON."""
        # Convert ISO strings back to datetime objects
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        # Convert string to enum
        data["status"] = JobStatus(data["status"])
        return cls(**data)


class JobManager:
    """Manages batch processing jobs using file-based storage."""

    def __init__(self, jobs_dir: Path = JOBS_DIR):
        """Initialize job manager.
        
        Args:
            jobs_dir: Directory to store job files
        """
        self.jobs_dir = jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JobManager initialized with jobs_dir: {self.jobs_dir}")

    def _get_job_path(self, job_id: str) -> Path:
        """Get file path for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Path to job file
        """
        return self.jobs_dir / f"{job_id}.json"

    def _read_job_file(self, job_path: Path) -> Dict[str, Any]:
        """Read job data from file with locking.
        
        Args:
            job_path: Path to job file
            
        Returns:
            Job data dictionary
            
        Raises:
            FileNotFoundError: If job file doesn't exist
        """
        with open(job_path, "r") as f:
            # Acquire shared lock for reading
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data

    def _write_job_file(self, job_path: Path, data: Dict[str, Any]) -> None:
        """Write job data to file with locking.
        
        Args:
            job_path: Path to job file
            data: Job data dictionary
        """
        # Write to temp file first, then atomic rename
        temp_path = job_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            # Acquire exclusive lock for writing
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        # Atomic rename
        temp_path.rename(job_path)

    def create_job(self, total_images: int) -> str:
        """Create a new batch job.
        
        Args:
            total_images: Number of images to process
            
        Returns:
            Job ID (UUID4)
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        job = BatchJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            total_images=total_images,
        )
        
        job_path = self._get_job_path(job_id)
        self._write_job_file(job_path, job.to_dict())
        
        logger.info(f"Created job {job_id} for {total_images} images")
        return job_id

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            BatchJob if found, None otherwise
        """
        job_path = self._get_job_path(job_id)
        
        if not job_path.exists():
            logger.warning(f"Job {job_id} not found")
            return None
        
        try:
            data = self._read_job_file(job_path)
            return BatchJob.from_dict(data)
        except Exception as e:
            logger.error(f"Error reading job {job_id}: {e}")
            return None

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        processed_images: Optional[int] = None,
        summary: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update job fields atomically.
        
        Args:
            job_id: Job identifier
            status: New status
            processed_images: New processed image count
            summary: Summary data (for completed jobs)
            error: Error message (for failed jobs)
            
        Returns:
            True if updated successfully, False otherwise
        """
        job_path = self._get_job_path(job_id)
        
        if not job_path.exists():
            logger.warning(f"Cannot update job {job_id}: not found")
            return False
        
        try:
            # Read current job data
            data = self._read_job_file(job_path)
            job = BatchJob.from_dict(data)
            
            # Update fields
            job.updated_at = datetime.utcnow()
            if status is not None:
                job.status = status
                if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                    job.completed_at = job.updated_at
            if processed_images is not None:
                job.processed_images = processed_images
            if summary is not None:
                job.summary = summary
            if error is not None:
                job.error = error
            
            # Write updated job
            self._write_job_file(job_path, job.to_dict())
            logger.debug(f"Updated job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False

    def append_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Append a single result to job's results list.
        
        Args:
            job_id: Job identifier
            result: Result dictionary for one image
            
        Returns:
            True if appended successfully, False otherwise
        """
        job_path = self._get_job_path(job_id)
        
        if not job_path.exists():
            logger.warning(f"Cannot append result to job {job_id}: not found")
            return False
        
        try:
            # Read current job data
            data = self._read_job_file(job_path)
            job = BatchJob.from_dict(data)
            
            # Append result and update counters
            job.results.append(result)
            job.processed_images = len(job.results)
            job.updated_at = datetime.utcnow()
            
            # Write updated job
            self._write_job_file(job_path, job.to_dict())
            logger.debug(f"Appended result to job {job_id} ({job.processed_images}/{job.total_images})")
            return True
        except Exception as e:
            logger.error(f"Error appending result to job {job_id}: {e}")
            return False

    def delete_job(self, job_id: str) -> bool:
        """Delete a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        job_path = self._get_job_path(job_id)
        
        if not job_path.exists():
            logger.warning(f"Cannot delete job {job_id}: not found")
            return False
        
        try:
            job_path.unlink()
            logger.info(f"Deleted job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def cleanup_old_jobs(self, retention_hours: int = 1) -> int:
        """Delete jobs older than retention period.
        
        Args:
            retention_hours: Hours to retain completed jobs
            
        Returns:
            Number of jobs deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        deleted_count = 0
        
        for job_file in self.jobs_dir.glob("*.json"):
            try:
                data = self._read_job_file(job_file)
                job = BatchJob.from_dict(data)
                
                # Only cleanup completed, failed, or cancelled jobs
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                    if job.completed_at and job.completed_at < cutoff_time:
                        job_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Cleaned up old job {job.job_id}")
            except Exception as e:
                logger.error(f"Error cleaning up job file {job_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old jobs")
        
        return deleted_count

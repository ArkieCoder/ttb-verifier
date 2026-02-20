"""Tests for QueueManager and async verify API endpoints."""
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# QueueManager unit tests (no FastAPI, no Ollama)
# ============================================================================

@pytest.fixture
def tmp_db(tmp_path):
    """A fresh QueueManager backed by a temp DB for each test."""
    # Import here so sys.path issues are isolated
    from queue_manager import QueueManager
    return QueueManager(db_path=tmp_path / "test_queue.db", max_attempts=3)


@pytest.fixture
def sample_image(tmp_path):
    """A tiny valid-looking image file."""
    p = tmp_path / "label.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # JPEG magic bytes
    return str(p)


class TestQueueManagerEnqueue:
    def test_enqueue_returns_job_id(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        assert isinstance(job_id, str) and len(job_id) == 36  # UUID4

    def test_enqueue_with_ground_truth(self, tmp_db, sample_image):
        gt = {"brand_name": "Acme Ale", "abv": 5.0}
        job_id = tmp_db.enqueue(sample_image, ground_truth=gt)
        job = tmp_db.get(job_id)
        assert job["ground_truth"] == gt

    def test_enqueue_without_ground_truth(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        job = tmp_db.get(job_id)
        assert job["ground_truth"] is None

    def test_enqueued_job_is_pending(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        job = tmp_db.get(job_id)
        assert job["status"] == "pending"
        assert job["attempts"] == 0

    def test_queue_depth_reflects_pending_count(self, tmp_db, sample_image):
        assert tmp_db.queue_depth() == 0
        tmp_db.enqueue(sample_image)
        assert tmp_db.queue_depth() == 1
        tmp_db.enqueue(sample_image)
        assert tmp_db.queue_depth() == 2


class TestQueueManagerDequeue:
    def test_dequeue_empty_returns_none(self, tmp_db):
        assert tmp_db.dequeue() is None

    def test_dequeue_claims_job(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        job = tmp_db.dequeue()
        assert job is not None
        assert job["id"] == job_id
        assert job["status"] == "processing"
        assert job["attempts"] == 1

    def test_dequeue_decrements_queue_depth(self, tmp_db, sample_image):
        tmp_db.enqueue(sample_image)
        tmp_db.enqueue(sample_image)
        assert tmp_db.queue_depth() == 2
        tmp_db.dequeue()
        assert tmp_db.queue_depth() == 1

    def test_dequeue_fifo_order(self, tmp_db, sample_image):
        id1 = tmp_db.enqueue(sample_image)
        time.sleep(0.01)
        id2 = tmp_db.enqueue(sample_image)
        first = tmp_db.dequeue()
        second = tmp_db.dequeue()
        assert first["id"] == id1
        assert second["id"] == id2

    def test_dequeue_returns_none_when_all_processing(self, tmp_db, sample_image):
        tmp_db.enqueue(sample_image)
        tmp_db.dequeue()  # claims the only job
        assert tmp_db.dequeue() is None


class TestQueueManagerComplete:
    def test_complete_marks_completed(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()
        result = {"status": "COMPLIANT", "processing_time_seconds": 9.5}
        tmp_db.complete(job_id, result)
        job = tmp_db.get(job_id)
        assert job["status"] == "completed"
        assert job["result"]["status"] == "COMPLIANT"
        assert job["completed_at"] is not None

    def test_complete_clears_error(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()
        tmp_db.fail(job_id, "transient error")
        # Re-dequeue after requeue
        tmp_db.dequeue()
        tmp_db.complete(job_id, {"status": "COMPLIANT"})
        job = tmp_db.get(job_id)
        assert job["error"] is None


class TestQueueManagerFail:
    def test_fail_requeues_when_attempts_remaining(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()  # attempts=1, max=3
        tmp_db.fail(job_id, "timeout")
        job = tmp_db.get(job_id)
        # Should go back to pending for retry
        assert job["status"] == "pending"
        assert job["error"] == "timeout"

    def test_fail_permanently_fails_after_max_attempts(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        # Exhaust all attempts
        for _ in range(3):
            tmp_db.dequeue()
            tmp_db.fail(job_id, "timeout")
        job = tmp_db.get(job_id)
        assert job["status"] == "failed"
        assert job["attempts"] == 3

    def test_fail_unknown_job_is_noop(self, tmp_db):
        # Should not raise
        tmp_db.fail("nonexistent-id", "error")


class TestQueueManagerCancel:
    def test_cancel_pending_job(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        cancelled = tmp_db.cancel(job_id)
        assert cancelled is True
        job = tmp_db.get(job_id)
        assert job["status"] == "cancelled"

    def test_cancel_processing_job_noop(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()
        cancelled = tmp_db.cancel(job_id)
        assert cancelled is False
        job = tmp_db.get(job_id)
        assert job["status"] == "processing"


class TestQueueManagerGet:
    def test_get_nonexistent_returns_none(self, tmp_db):
        assert tmp_db.get("does-not-exist") is None

    def test_get_returns_full_job(self, tmp_db, sample_image):
        gt = {"abv": 7.5}
        job_id = tmp_db.enqueue(sample_image, ground_truth=gt)
        job = tmp_db.get(job_id)
        assert job["id"] == job_id
        assert job["image_path"] == sample_image
        assert job["ground_truth"] == gt
        assert job["max_attempts"] == 3


class TestQueueManagerCleanup:
    def test_cleanup_removes_old_terminal_jobs(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()
        tmp_db.complete(job_id, {"status": "COMPLIANT"})

        # Cleanup with 0-second retention should remove it
        count = tmp_db.cleanup_old_jobs(retention_seconds=0)
        assert count == 1
        assert tmp_db.get(job_id) is None

    def test_cleanup_keeps_recent_jobs(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        tmp_db.dequeue()
        tmp_db.complete(job_id, {"status": "COMPLIANT"})

        # Cleanup with 1-hour retention should keep it
        count = tmp_db.cleanup_old_jobs(retention_seconds=3600)
        assert count == 0
        assert tmp_db.get(job_id) is not None

    def test_cleanup_does_not_remove_pending_jobs(self, tmp_db, sample_image):
        job_id = tmp_db.enqueue(sample_image)
        count = tmp_db.cleanup_old_jobs(retention_seconds=0)
        assert count == 0
        assert tmp_db.get(job_id) is not None


# ============================================================================
# Async verify API endpoint tests
# ============================================================================

@pytest.fixture
def client():
    from api import app
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    from auth import create_session_cookie, SESSION_COOKIE_NAME
    session_cookie = create_session_cookie("testuser")
    client.cookies.set(SESSION_COOKIE_NAME, session_cookie)
    return client


@pytest.fixture
def sample_image_bytes(good_label_path):
    if not good_label_path.exists():
        pytest.skip(f"Sample image not found: {good_label_path}")
    return good_label_path.read_bytes()


@pytest.fixture
def patched_queue(tmp_path):
    """
    Patch verify_queue in both api and ui_routes modules with a fresh
    QueueManager backed by a temp DB.
    """
    from queue_manager import QueueManager
    q = QueueManager(db_path=tmp_path / "api_test_queue.db", max_attempts=3)
    with patch("api.verify_queue", q), patch("ui_routes.verify_queue", q, create=True):
        yield q


class TestAsyncVerifySubmit:
    def test_submit_returns_job_id(self, authenticated_client, sample_image_bytes, patched_queue, tmp_path):
        with patch("api.settings") as mock_settings:
            mock_settings.queue_db_path = str(tmp_path / "api_test_queue.db")
            mock_settings.queue_max_attempts = 3
            mock_settings.ollama_timeout_seconds = 60
            mock_settings.max_file_size_mb = 10
            mock_settings.max_file_size_bytes = 10 * 1024 * 1024
            # Use actual validate_image_file path
            response = authenticated_client.post(
                "/verify/async",
                files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
            )
        # Should accept and enqueue
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_submit_invalid_file_type_rejected(self, authenticated_client, patched_queue):
        response = authenticated_client.post(
            "/verify/async",
            files={"image": ("doc.txt", b"not an image", "text/plain")},
        )
        assert response.status_code == 400

    def test_submit_missing_image_rejected(self, authenticated_client, patched_queue):
        response = authenticated_client.post("/verify/async")
        assert response.status_code == 422

    def test_submit_unauthenticated_rejected(self, client, sample_image_bytes, patched_queue):
        response = client.post(
            "/verify/async",
            files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code in (401, 302, 403)


class TestAsyncVerifyStatus:
    def test_status_pending_job(self, authenticated_client, sample_image_bytes, patched_queue, tmp_path):
        # Enqueue directly via the queue
        img = tmp_path / "label.jpg"
        img.write_bytes(sample_image_bytes)
        job_id = patched_queue.enqueue(str(img))

        response = authenticated_client.get(f"/verify/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"
        assert "queue_depth" in data

    def test_status_completed_job_includes_result(self, authenticated_client, patched_queue, tmp_path):
        img = tmp_path / "label.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)
        job_id = patched_queue.enqueue(str(img))
        patched_queue.dequeue()

        fake_result = {
            "status": "COMPLIANT",
            "validation_level": "STRUCTURAL_ONLY",
            "extracted_fields": {},
            "validation_results": {"structural": [], "accuracy": []},
            "violations": [],
            "warnings": [],
            "processing_time_seconds": 9.1,
        }
        patched_queue.complete(job_id, fake_result)

        response = authenticated_client.get(f"/verify/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["status"] == "COMPLIANT"

    def test_status_failed_job(self, authenticated_client, patched_queue, tmp_path):
        img = tmp_path / "label.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)
        job_id = patched_queue.enqueue(str(img))
        # Exhaust all attempts
        for _ in range(3):
            patched_queue.dequeue()
            patched_queue.fail(job_id, "Ollama timeout")

        response = authenticated_client.get(f"/verify/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Ollama timeout" in data["error"]

    def test_status_not_found(self, authenticated_client, patched_queue):
        response = authenticated_client.get("/verify/status/nonexistent-job-id")
        assert response.status_code == 404

    def test_status_unauthenticated(self, client, patched_queue):
        response = client.get("/verify/status/some-job-id")
        assert response.status_code in (401, 302, 403)

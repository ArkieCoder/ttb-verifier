"""
Unit tests for prewarm_ollama_model().

The pre-warm function is responsible for loading the Ollama model into GPU
RAM exactly once across all 4 uvicorn workers. The key correctness properties:

  1. If the model is already in GPU (/api/ps says so), skip — no chat call.
  2. If the done-file exists, skip — another worker already succeeded.
  3. If another worker holds the file lock, skip gracefully.
  4. Happy path: acquire lock, call /api/chat, write done-file.
  5. HTTP failure from /api/chat: do NOT write done-file (allow retry).
  6. /api/ps failure: fall through and attempt the pre-warm anyway.
  7. In-process guard: if _ollama_prewarmed is already True, return immediately.
"""
import fcntl
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

import api


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_prewarm_state():
    """Reset module-level pre-warm flags between tests."""
    api._ollama_prewarmed = False
    api._ollama_prewarm_lock = False


def _run_prewarm_sync(ollama_host="http://ollama:11434", model="llama3.2-vision",
                      tmp_path=None):
    """
    Call prewarm_ollama_model and wait for its background thread to finish.

    The function spawns a daemon thread; we need to join it so assertions
    run after the work is done.  We monkey-patch threading.Thread to capture
    the thread and join it here.
    """
    captured = {}

    real_thread_init = threading.Thread.__init__

    def patched_init(self, *args, **kwargs):
        real_thread_init(self, *args, **kwargs)
        captured['thread'] = self

    with patch.object(threading.Thread, '__init__', patched_init):
        api.prewarm_ollama_model(ollama_host, model)

    thread = captured.get('thread')
    if thread:
        thread.join(timeout=5)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state(tmp_path):
    """
    Before every test: reset in-process flags and redirect file paths to a
    temp directory so tests are isolated and don't touch /app/tmp.
    """
    _reset_prewarm_state()

    lock_file = tmp_path / "prewarm.lock"
    done_file = tmp_path / "prewarm.done"

    with patch.object(api, '_PREWARM_LOCK_FILE', lock_file), \
         patch.object(api, '_PREWARM_DONE_FILE', done_file):
        yield {'lock_file': lock_file, 'done_file': done_file}

    # Reset again after test in case the test left flags dirty
    _reset_prewarm_state()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_skips_when_model_already_in_gpu(reset_state):
    """If /api/ps reports the model loaded, skip /api/chat entirely."""
    done_file = reset_state['done_file']

    ps_response = MagicMock()
    ps_response.status_code = 200
    ps_response.json.return_value = {
        'models': [{'name': 'llama3.2-vision:latest'}]
    }

    with patch('requests.get', return_value=ps_response) as mock_get, \
         patch('requests.post') as mock_post:
        _run_prewarm_sync()

    mock_post.assert_not_called()
    assert api._ollama_prewarmed is True
    assert done_file.exists(), "done-file must be written so other workers skip"


def test_skips_when_done_file_exists(reset_state):
    """If the done-file is already present, skip all network calls."""
    done_file = reset_state['done_file']
    done_file.touch()

    ps_response = MagicMock()
    ps_response.status_code = 200
    ps_response.json.return_value = {'models': []}  # model NOT in GPU

    with patch('requests.get', return_value=ps_response), \
         patch('requests.post') as mock_post:
        _run_prewarm_sync()

    mock_post.assert_not_called()
    assert api._ollama_prewarmed is True


def test_happy_path_calls_generate_and_writes_done_file(reset_state):
    """Happy path: no model in GPU, no done-file → call /api/generate, write done-file.

    We use /api/generate with an empty prompt and keep_alive=-1 rather than
    /api/chat with a real message.  /api/chat runs full inference (20-60s) and
    blocks Ollama's single inference thread, which causes /api/tags health-check
    calls to hang and cascading 503s from CloudFront.  /api/generate with an
    empty prompt loads the weights without real inference.
    """
    done_file = reset_state['done_file']

    ps_response = MagicMock()
    ps_response.status_code = 200
    ps_response.json.return_value = {'models': []}

    generate_response = MagicMock()
    generate_response.status_code = 200

    with patch('requests.get', return_value=ps_response), \
         patch('requests.post', return_value=generate_response) as mock_post:
        _run_prewarm_sync()

    # Verify /api/generate was called with the right payload
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert '/api/generate' in call_args[0][0]
    payload = call_args[1]['json']
    assert payload['model'] == 'llama3.2-vision'
    assert payload['keep_alive'] == -1
    assert payload['stream'] is False
    assert payload['prompt'] == ''

    assert api._ollama_prewarmed is True
    assert done_file.exists(), "done-file must be written after successful pre-warm"


def test_failed_generate_request_does_not_write_done_file(reset_state):
    """If /api/generate returns an error, done-file must NOT be written (allow retry)."""
    done_file = reset_state['done_file']

    ps_response = MagicMock()
    ps_response.status_code = 200
    ps_response.json.return_value = {'models': []}

    chat_response = MagicMock()
    chat_response.status_code = 500

    with patch('requests.get', return_value=ps_response), \
         patch('requests.post', return_value=chat_response):
        _run_prewarm_sync()

    assert not done_file.exists(), "done-file must NOT exist after a failed pre-warm"
    assert api._ollama_prewarmed is False


def test_ps_failure_falls_through_to_prewarm(reset_state):
    """/api/ps connection error should not abort — fall through and try /api/generate."""
    import requests as req

    generate_response = MagicMock()
    generate_response.status_code = 200

    with patch('requests.get', side_effect=req.exceptions.ConnectionError("refused")), \
         patch('requests.post', return_value=generate_response) as mock_post:
        _run_prewarm_sync()

    mock_post.assert_called_once()
    assert api._ollama_prewarmed is True


def test_in_process_guard_prevents_double_fire(reset_state):
    """If _ollama_prewarmed is already True, return without spawning a thread."""
    api._ollama_prewarmed = True

    with patch('threading.Thread') as mock_thread:
        api.prewarm_ollama_model("http://ollama:11434", "llama3.2-vision")

    mock_thread.assert_not_called()


def test_lock_contention_skips_gracefully(reset_state, tmp_path):
    """
    If another process already holds the exclusive lock on the lock-file,
    this worker should skip without raising and without calling /api/chat.
    """
    lock_file = reset_state['lock_file']
    lock_file.touch()

    # Acquire the exclusive lock in this test process, simulating a competing worker
    fd = open(lock_file, 'w')
    fcntl.flock(fd.fileno(), fcntl.LOCK_EX)

    try:
        ps_response = MagicMock()
        ps_response.status_code = 200
        ps_response.json.return_value = {'models': []}

        with patch('requests.get', return_value=ps_response), \
             patch('requests.post') as mock_post:
            _run_prewarm_sync()

        mock_post.assert_not_called()
    finally:
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        fd.close()

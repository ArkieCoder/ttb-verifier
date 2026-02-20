"""Integration tests - CLI behavior."""
import subprocess
import json
import pytest


def test_cli_help():
    """Test CLI help command."""
    result = subprocess.run(
        ["python3", "verify_label.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_missing_file():
    """Test CLI with missing file."""
    result = subprocess.run(
        ["python3", "verify_label.py", "nonexistent.jpg"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0


def test_cli_with_sample(good_label_path):
    """Test CLI produces valid JSON output for a real sample image.

    Ollama is not available in the test environment, so the result may have
    status='ERROR' and exit code 1, but the CLI must always emit well-formed
    JSON containing the required top-level fields.
    """
    if not good_label_path.exists():
        pytest.skip("Golden sample not available")

    result = subprocess.run(
        ["python3", "verify_label.py", str(good_label_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )

    # CLI must produce output regardless of Ollama availability
    assert result.stdout.strip(), (
        f"CLI produced no stdout:\nstderr: {result.stderr}"
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"CLI did not output valid JSON:\n{result.stdout}")

    assert "status" in data, "Result missing 'status' field"
    assert "extracted_fields" in data, "Result missing 'extracted_fields' field"
    assert "validation_results" in data, "Result missing 'validation_results' field"

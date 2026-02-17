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


@pytest.mark.slow
def test_cli_with_sample(good_label_path):
    """Test CLI with actual sample image."""
    if not good_label_path.exists():
        pytest.skip("Golden sample not available")
    
    result = subprocess.run(
        ["python3", "verify_label.py", str(good_label_path)],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should produce valid JSON
    try:
        data = json.loads(result.stdout)
        assert 'status' in data
        assert 'extracted_fields' in data
    except json.JSONDecodeError:
        pytest.fail("CLI did not output valid JSON")

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_inlined_stadium_matches_generator():
    result = subprocess.run([sys.executable, 'tools/stadium.py', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout

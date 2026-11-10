"""Puts scripts/ on sys.path so the tests can `import changelog`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

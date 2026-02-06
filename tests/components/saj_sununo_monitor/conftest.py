"""Fixtures for SAJ Sununo-TL Series Monitor tests."""

from __future__ import annotations

from pathlib import Path
import sys

# Add config path to sys.path so we can import custom components
config_path = Path(__file__).parent.parent.parent.parent / "config"
if str(config_path) not in sys.path:
    sys.path.insert(0, str(config_path))

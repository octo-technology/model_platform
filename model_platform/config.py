"""Configuration module for the model platform.

This module defines the project directory path.
"""

from pathlib import Path

PROJECT_DIR: Path = Path(__file__).parent.parent.resolve()

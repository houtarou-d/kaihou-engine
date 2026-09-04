"""Utility functions for loading YAML configuration files.

The engine expects configuration under the ``config/`` directory.  Each
helper returns a Python ``dict`` (or a parsed Pydantic model when the
caller wishes).
"""

from pathlib import Path
from typing import Any, Dict

import yaml

def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Read a YAML file and return its contents as a ``dict``.

    If the file does not exist or is empty, an empty dict is returned.
    """
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def get_config_dir() -> Path:
    """Return the absolute path to the ``config`` directory of the repo."""
    return Path(__file__).resolve().parents[2] / "config"


__all__ = ["load_yaml_file", "get_config_dir"]

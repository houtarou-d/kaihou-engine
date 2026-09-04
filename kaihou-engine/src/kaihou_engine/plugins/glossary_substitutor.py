"""Glossary substitutor plugin.

The plugin reads the `glossaries.yaml` configuration (based on the target
language) and replaces matching terms in the string values of the analysis
result.

The orchestrator expects a callable named ``process`` that receives a
``dict`` (the current pipeline data) and returns the possibly‑modified
``dict``.
"""

import json
from pathlib import Path
from typing import Any, Dict

import yaml

def _load_glossary(lang: str) -> Dict[str, str]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "glossaries.yaml"
    if not config_path.is_file():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get(lang, {})

def process(data: Dict[str, Any], *, target_language: str = "en") -> Dict[str, Any]:
    """Replace terms in ``data`` according to the glossary for ``target_language``.

    The function walks the mapping recursively and substitutes any string
    value that exactly matches a source term.  It returns the modified data.
    """
    glossary = _load_glossary(target_language)
    if not glossary:
        return data

    def replace(value: Any) -> Any:
        if isinstance(value, str):
            return glossary.get(value, value)
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        return value

    return replace(data)

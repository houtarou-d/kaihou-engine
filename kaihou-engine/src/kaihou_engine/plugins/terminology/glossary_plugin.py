"""Glossary plugin implementing TerminologyPlugin.

It reads the ``config/glossaries.yaml`` file and builds a ``TerminologyContext``
object that the pipeline can attach to the ``TranslationRequest``.
"""

from ...core.schemas import TerminologyContext, TerminologyHit, DictionaryEntry

from ..base import TerminologyPlugin

import yaml
from pathlib import Path

class GlossaryPlugin(TerminologyPlugin):
    def __init__(self) -> None:
        # Load glossaries once at construction time.
        self.glossaries_path = Path(__file__).resolve().parents[3] / "config" / "glossaries.yaml"
        self._glossaries = self._load_glossaries()

    def _load_glossaries(self):
        if not self.glossaries_path.is_file():
            return {}
        with self.glossaries_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def query(self, analysis, domain: str | None = None):
        # For this simple implementation we ignore the analysis content
        # and just return the raw glossary data converted to the Pydantic model.
        hits = []
        entries = []
        for lang, data in self._glossaries.items():
            # ``data`` may be a dict with ``terminology_hits``/``dictionary_entries``
            if isinstance(data, dict):
                # Assume a flat mapping of source->target for forced terms
                for src, tgt in data.get("terms", {}).items():
                    hits.append(TerminologyHit(source_term=src, forced_translation=tgt, domain=lang))
                # Dictionary entries – optional, not used in this simple plugin
                for term, defs in data.get("dictionary", {}).items():
                    entries.append(DictionaryEntry(term=term, definitions=defs, part_of_speech="", examples=[]))
        return TerminologyContext(terminology_hits=hits, dictionary_entries=entries, cultural_notes=[], regional_variant=None)

__all__ = ["GlossaryPlugin"]

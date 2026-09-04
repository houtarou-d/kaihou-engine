"""Abstract base classes for Kaihou Engine plugins.

Each plugin type defines a contract that the concrete implementation must
follow.  Plugins are discovered via the ``plugins.yaml`` configuration
file and instantiated by ``plugin_registry``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from ..core.schemas import (
    SourceAnalysis,
    TerminologyContext,
    TranslationRequest,
    LLMDraft,
    DecisionResult,
    ValidationReport,
)


class NLPEnginePlugin(ABC):
    @abstractmethod
    def analyze(self, text: str, lang: str) -> SourceAnalysis:
        """Run the underlying NLP engine (e.g., ``kaihou-nlp-engine``) and
        return a validated ``SourceAnalysis`` instance.
        """


class TerminologyPlugin(ABC):
    @abstractmethod
    def query(self, analysis: SourceAnalysis, domain: str | None) -> TerminologyContext:
        """Return terminology information (glossary hits, dictionary entries,
        cultural notes, …) for a given analysis.
        """


class LLMConnectorPlugin(ABC):
    @abstractmethod
    async def translate(self, request: TranslationRequest) -> LLMDraft:
        """Generate a translation draft for ``request``.
        Returns a ``LLMDraft`` containing the raw translated text.
        """

    @abstractmethod
    async def decide(self, request: TranslationRequest, drafts: List[LLMDraft]) -> DecisionResult:
        """Given a list of drafts, pick the best translation and return a
        ``DecisionResult``.  Only connectors that implement the ``decider``
        role need to provide this method; others may raise ``NotImplementedError``.
        """


class ValidatorPlugin(ABC):
    @abstractmethod
    def validate(self, request: TranslationRequest, result_analysis: SourceAnalysis) -> ValidationReport:
        """Validate the translated text (via a re‑analysis) and produce a
        ``ValidationReport``.
        """


__all__ = [
    "NLPEnginePlugin",
    "TerminologyPlugin",
    "LLMConnectorPlugin",
    "ValidatorPlugin",
]

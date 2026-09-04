"""Semantic similarity validator plugin.

Computes a cosine similarity between the source and translated sentences
using a multilingual sentence‑transformers model.  If the similarity
falls below a configurable threshold (default 0.80) a ``warning`` issue
is emitted.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from ..base import ValidatorPlugin
from ...core.schemas import ValidationIssue, ValidationReport, SourceAnalysis, TranslationRequest


class SemanticValidator(ValidatorPlugin):
    def __init__(self, *, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", threshold: float = 0.80) -> None:
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold

    def _embed(self, text: str) -> np.ndarray:
        # Convert to 1‑D torch tensor, then to numpy for cosine.
        vec = self.model.encode(text, convert_to_numpy=True)
        return vec / np.linalg.norm(vec)

    def validate(self, request: TranslationRequest, result_analysis: SourceAnalysis) -> ValidationReport:
        src_emb = self._embed(request.source_text)
        tgt_text = " ".join(t.text for t in result_analysis.tokens)
        tgt_emb = self._embed(tgt_text)
        similarity = float(np.dot(src_emb, tgt_emb))
        issues = []
        if similarity < self.threshold:
            issues.append(
                ValidationIssue(
                    type="low_semantic_similarity",
                    severity="warning",
                    detail=f"Semantic similarity {similarity:.2f} below threshold {self.threshold:.2f}.",
                )
            )
        return ValidationReport(passed=not issues, issues=issues, semantic_similarity_score=similarity)


__all__ = ["SemanticValidator"]

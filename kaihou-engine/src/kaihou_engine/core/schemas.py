"""Pydantic schemas for Kaihou Engine.

These models follow the specification in `kaihou_spec.md` (section 4).
They are used throughout the pipeline to validate data exchanged between
plugins, the NLP engine, and the final CLI output.
"""

from __future__ import annotations

from typing import List, Dict, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Token and NamedEntity models (used by SourceAnalysis)
# ---------------------------------------------------------------------------

class Token(BaseModel):
    text: str
    lemma: str
    pos: str  # UPOS tag (NOUN, VERB, ADJ, ...)
    tag: str  # language‑specific detailed tag
    morph: Dict[str, str]
    dep: str  # dependency relation
    head_index: int
    index: int


class NamedEntity(BaseModel):
    text: str
    label: str  # PERSON, ORG, DATE, GPE, etc.
    start_char: int
    end_char: int


# ---------------------------------------------------------------------------
# 2. SourceAnalysis – output of the NLP engine (kaihou‑nlp‑engine)
# ---------------------------------------------------------------------------

class SourceAnalysis(BaseModel):
    raw_text: str
    language: str  # "fr" | "en"
    tokens: List[Token]
    entities: List[NamedEntity]
    sentences: List[str]
    register: Optional[str] = None
    tone: Optional[str] = None
    domain: Optional[str] = None


# ---------------------------------------------------------------------------
# 3. Terminology related models
# ---------------------------------------------------------------------------

class TerminologyHit(BaseModel):
    source_term: str
    forced_translation: Optional[str] = None
    domain: str
    notes: Optional[str] = None


class DictionaryEntry(BaseModel):
    term: str
    definitions: List[str]
    part_of_speech: str
    examples: List[str] = []


class TerminologyContext(BaseModel):
    terminology_hits: List[TerminologyHit]
    dictionary_entries: List[DictionaryEntry]
    cultural_notes: List[str] = []
    regional_variant: Optional[str] = None


# ---------------------------------------------------------------------------
# 4. Translation request / draft / decision models
# ---------------------------------------------------------------------------

class TranslationRequest(BaseModel):
    source_text: str
    source_lang: str
    target_lang: str
    analysis: SourceAnalysis
    terminology: TerminologyContext
    instructions: List[str] = []


class LLMDraft(BaseModel):
    llm_id: str
    role: Literal["draft", "specialist", "decider"]
    translated_text: str
    self_notes: Optional[str] = None


class DecisionResult(BaseModel):
    final_translation: str
    reasoning: str
    chosen_from: Dict[str, str]
    confidence: Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# 5. Validation report models
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    type: Literal[
        "missing_number",
        "missing_entity",
        "added_content",
        "terminology_violation",
        "structure_mismatch",
        "low_semantic_similarity",
    ]
    severity: Literal["critical", "warning", "info"]
    detail: str


class ValidationReport(BaseModel):
    passed: bool
    issues: List[ValidationIssue]
    semantic_similarity_score: Optional[float] = None


# Export public symbols for easy import elsewhere
__all__ = [
    "Token",
    "NamedEntity",
    "SourceAnalysis",
    "TerminologyHit",
    "DictionaryEntry",
    "TerminologyContext",
    "TranslationRequest",
    "LLMDraft",
    "DecisionResult",
    "ValidationIssue",
    "ValidationReport",
]

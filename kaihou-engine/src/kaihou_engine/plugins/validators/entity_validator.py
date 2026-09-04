"""Entity validator plugin.

Ensures that every named entity (PERSON, ORG, DATE, GPE, …) detected in
the source text also appears in the translated text.  Missing entities are
reported as ``critical`` issues.
"""

from ..base import ValidatorPlugin
from ...core.schemas import ValidationIssue, ValidationReport, SourceAnalysis, TranslationRequest



class EntityValidator(ValidatorPlugin):
    def validate(self, request: TranslationRequest, result_analysis: SourceAnalysis) -> ValidationReport:
        src_entities = {(e.text, e.label) for e in request.analysis.entities}
        tgt_entities = {(e.text, e.label) for e in result_analysis.entities}
        missing = src_entities - tgt_entities
        issues = []
        for text, label in missing:
            issues.append(
                ValidationIssue(
                    type="missing_entity",
                    severity="critical",
                    detail=f"Entity '{text}' ({label}) missing in translation.",
                )
            )
        return ValidationReport(passed=not issues, issues=issues)


__all__ = ["EntityValidator"]

"""Terminology validator plugin.

Verifies that all ``forced_translation`` entries defined in the
``TerminologyContext`` appear verbatim in the translated text.  Violations
are reported as ``critical`` issues.
"""

from ..base import ValidatorPlugin
from ...core.schemas import ValidationIssue, ValidationReport, SourceAnalysis, TranslationRequest



class TerminologyValidator(ValidatorPlugin):
    def validate(self, request: TranslationRequest, result_analysis: SourceAnalysis) -> ValidationReport:
        forced = {
            hit.forced_translation
            for hit in request.terminology.terminology_hits
            if hit.forced_translation
        }
        # Flatten the translated text into a single string for simple containment checks.
        translated_text = " ".join(t.text for t in result_analysis.tokens)
        issues = []
        for term in forced:
            if term not in translated_text:
                issues.append(
                    ValidationIssue(
                        type="terminology_violation",
                        severity="critical",
                        detail=f"Forced term '{term}' not found in translation.",
                    )
                )
        return ValidationReport(passed=not issues, issues=issues)


__all__ = ["TerminologyValidator"]

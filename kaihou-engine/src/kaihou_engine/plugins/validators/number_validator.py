"""Number validator plugin.

Checks that every numerical token present in the source text also appears in
the translated text (after re‑analysis).  Missing numbers are reported as a
critical ``ValidationIssue``.
"""

from ..base import ValidatorPlugin
from ...core.schemas import ValidationIssue, ValidationReport, SourceAnalysis, TranslationRequest



class NumberValidator(ValidatorPlugin):
    def validate(self, request: TranslationRequest, result_analysis: SourceAnalysis) -> ValidationReport:
        # Extract numeric strings from source and target analyses.
        src_numbers = {t.text for t in request.analysis.tokens if t.text.isdigit()}
        tgt_numbers = {t.text for t in result_analysis.tokens if t.text.isdigit()}
        missing = src_numbers - tgt_numbers
        issues = []
        for num in missing:
            issues.append(
                ValidationIssue(
                    type="missing_number",
                    severity="critical",
                    detail=f"Number '{num}' present in source but absent in translation.",
                )
            )
        return ValidationReport(passed=not issues, issues=issues)


__all__ = ["NumberValidator"]

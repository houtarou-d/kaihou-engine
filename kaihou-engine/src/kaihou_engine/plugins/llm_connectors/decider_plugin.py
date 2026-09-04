"""Simple decider plugin.

It receives a list of ``LLMDraft`` objects and selects the one with the
longest translated text (as a naive quality heuristic).  It returns a
``DecisionResult`` model.
"""

from ..base import LLMConnectorPlugin
from ..base import DecisionResult, TranslationRequest, LLMDraft

class SimpleDecider(LLMConnectorPlugin):
    def __init__(self, *, role: str = "decider") -> None:
        self.role = role

    async def translate(self, request):
        raise NotImplementedError("Decider plugin does not implement translate")

    async def decide(self, request: TranslationRequest, drafts: list[LLMDraft]):
        # Pick the draft with the longest translation text.
        best = max(drafts, key=lambda d: len(d.translated_text))
        return DecisionResult(
            final_translation=best.translated_text,
            reasoning=f"Selected draft from {best.llm_id} (longest output).",
            chosen_from={"selected": best.llm_id},
            confidence="medium",
        )

__all__ = ["SimpleDecider"]

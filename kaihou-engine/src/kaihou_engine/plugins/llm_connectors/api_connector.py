"""API‑based LLM connector (e.g., OpenAI, Anthropic) plugin.

The connector sends a JSON payload to a generic HTTP endpoint that
conforms to the OpenAI‑compatible chat completion API.  It supports both
``translate`` (draft) and ``decide`` (decider) roles.
"""

import json
from typing import Any, Dict, List

import httpx

from ..base import LLMConnectorPlugin
from ..base import TranslationRequest, LLMDraft, DecisionResult


class ApiConnector(LLMConnectorPlugin):
    def __init__(
        self,
        *,
        endpoint: str,
        model_name: str,
        api_key: str | None = None,
        role: str = "draft",
    ) -> None:
        self.endpoint = endpoint.rstrip('/')
        self.model_name = model_name
        self.role = role
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self.client = httpx.AsyncClient(base_url=self.endpoint, headers=headers, timeout=30.0)

    async def translate(self, request: TranslationRequest) -> LLMDraft:
        if self.role != "draft":
            raise NotImplementedError("ApiConnector translate is only for draft role")
        payload = self._build_chat_payload(request)
        resp = await self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Assume the first choice's message content is the translation.
        message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMDraft(
            llm_id=self.model_name,
            role=self.role,
            translated_text=message.strip(),
            self_notes=None,
        )

    async def decide(self, request: TranslationRequest, drafts: List[LLMDraft]) -> DecisionResult:
        if self.role != "decider":
            raise NotImplementedError("ApiConnector decide is only for decider role")
        # Build a combined prompt that includes each draft and asks to pick the best.
        drafts_text = "\n\n".join(
            f"Draft {i+1} (by {d.llm_id}):\n{d.translated_text}" for i, d in enumerate(drafts)
        )
        system_prompt = (
            "You are a decision LLM. Choose the best translation among the drafts. "
            "Return a JSON object with fields: final_translation, reasoning, chosen_from, confidence."
        )
        user_prompt = (
            f"Source ({request.source_lang}): {request.source_text}\n\n"
            f"Target language: {request.target_lang}\n\n"
            f"Drafts:{drafts_text}\n"
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
        }
        resp = await self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        message = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        # The LLM is instructed to emit pure JSON – parse it safely.
        try:
            decision_dict = json.loads(message)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Decider LLM returned invalid JSON: {exc}\nRaw: {message}") from exc
        return DecisionResult(**decision_dict)

    def _build_chat_payload(self, request: TranslationRequest) -> Dict[str, Any]:
        system = (
            f"You are a translation assistant. Translate from {request.source_lang} to {request.target_lang}. "
            "Return only the translated text, no explanations."
        )
        user = request.source_text
        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
        }

    async def aclose(self) -> None:
        await self.client.aclose()


__all__ = ["ApiConnector"]

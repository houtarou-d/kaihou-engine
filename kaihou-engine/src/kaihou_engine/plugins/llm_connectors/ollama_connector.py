"""Ollama connector plugin (LLMConnectorPlugin implementation).

This is a minimal asynchronous wrapper around the Ollama HTTP API.  It
assumes an Ollama server is reachable at ``http://localhost:11434``.  The
connector sends a JSON payload with ``model`` and ``prompt`` and expects a
JSON response containing ``response`` (the generated text).

The implementation focuses on the ``translate`` method; ``decide`` raises
``NotImplementedError`` because the decider role will typically use an
API‑based connector (e.g., Claude).
"""

import json
from typing import Any, Dict

import httpx

from ..base import LLMConnectorPlugin
from ..base import TranslationRequest, LLMDraft


import os
from ...core.exceptions import PluginError


class OllamaConnector(LLMConnectorPlugin):
    def __init__(self, *, endpoint: str | None = None, model_name: str | None = None) -> None:
        # Default to the Ollama server the user described.
        self.endpoint = (endpoint or os.getenv("OLLAMA_ENDPOINT", "http://0.0.0.0:11434")).rstrip('/')
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud")
        self.client = httpx.AsyncClient(base_url=self.endpoint, timeout=30.0)

    async def translate(self, request: TranslationRequest) -> LLMDraft:
        prompt = self._build_prompt(request)
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        try:
            resp = await self.client.post("/api/generate", json=payload)
            resp.raise_for_status()
        except httpx.RequestError as exc:
            raise PluginError(f"Failed to contact Ollama at {self.endpoint}: {exc}")
        except httpx.HTTPStatusError as exc:
            raise PluginError(f"Ollama returned error {exc.response.status_code}: {exc.response.text}")
        data = resp.json()
        generated: str = data.get("response", "")
        return LLMDraft(
            llm_id=self.model_name,
            role="draft",
            translated_text=generated.strip(),
            self_notes=None,
        )

    async def decide(self, request: TranslationRequest, drafts: list[LLMDraft]):
        raise NotImplementedError("OllamaConnector does not implement a decider role")

    def _build_prompt(self, request: TranslationRequest) -> str:
        # Simple prompt: ask Ollama to translate preserving terminology.
        # In a real implementation we would inject glossary, register, tone, etc.
        return (
            f"Translate the following {request.source_lang} text to {request.target_lang}:\n\n"
            f"{request.source_text}\n\n"
            "Return only the translated sentence, no explanations."
        )

    async def aclose(self) -> None:
        await self.client.aclose()


__all__ = ["OllamaConnector"]

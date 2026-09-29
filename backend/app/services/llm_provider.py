"""
LLMProvider interface. Every part of the app that needs a completion goes
through `.complete(system, user) -> str`. Swap providers via .env
(LLM_PROVIDER) — no other code changes.

    LLMProvider
    ├── OpenAICompatibleProvider   (OpenAI, or any OpenAI-compatible endpoint)
    ├── GroqProvider               (OpenAI-compatible API, different base_url)
    ├── GeminiProvider
    └── RuleBasedProvider          (no API key needed — used for LLM_PROVIDER=rulebased,
                                     which is the out-of-the-box default so the MVP
                                     runs before you've configured any key)
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod

import httpx

from app.config.settings import Settings


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, json_mode: bool = False) -> str: ...


class OpenAICompatibleProvider(LLMProvider):
    """Works for OpenAI directly, and for Groq (OpenAI-compatible /chat/completions)."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        body = {
            "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
        }
        if json_mode:
            body["generationConfig"] = {"response_mime_type": "application/json"}
        resp = httpx.post(url, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


class RuleBasedProvider(LLMProvider):
    """
    No API key required. Used as the zero-config default so `git clone -> pip
    install -> run` works immediately (requirement #5). This is intentionally
    NOT a language model — it's a template-based stand-in that the real
    intent/sql modules fall back to when no LLM_API_KEY is configured. Once
    you set LLM_PROVIDER=openai (or groq/gemini) and LLM_API_KEY, real
    generation takes over automatically.
    """
    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        raise NotImplementedError(
            "RuleBasedProvider does not call an LLM. Callers (intent/sql modules) "
            "should check `isinstance(provider, RuleBasedProvider)` and use their "
            "own template logic instead of calling .complete()."
        )


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.LLM_PROVIDER == "openai":
        base_url = settings.LLM_BASE_URL or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(settings.LLM_API_KEY, settings.LLM_MODEL, base_url)
    if settings.LLM_PROVIDER == "groq":
        base_url = settings.LLM_BASE_URL or "https://api.groq.com/openai/v1"
        return OpenAICompatibleProvider(settings.LLM_API_KEY, settings.LLM_MODEL, base_url)
    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider(settings.LLM_API_KEY, settings.LLM_MODEL)
    if settings.LLM_PROVIDER == "rulebased":
        return RuleBasedProvider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")


def try_parse_json(raw: str) -> dict | None:
    """Defensively parses JSON from LLM outputs even if wrapped in fences or prose."""
    import re
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip()

    # 1. Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Try stripping markdown code fences
    match_fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match_fence:
        try:
            return json.loads(match_fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Try finding outermost { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        snippet = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    return None

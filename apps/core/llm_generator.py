"""Replaceable text-generation adapters shared by application frontends."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import threading
import time
from typing import Protocol

import requests


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> str: ...


class CallableTextGenerator:
    def __init__(self, function: Callable[[str], str]) -> None:
        self.function = function
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        return self.function(prompt)


class GeminiTextGenerator:
    """Gemini adapter using a rotating file-backed API-key pool."""

    def __init__(
        self,
        model: str,
        max_output_tokens: int | None = None,
        thinking_budget: int = 0,
        thinking_level: str = "low",
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
        api_keys_file: str | Path = "apps/api/secrets/gemini_api_keys.txt",
    ) -> None:
        if not model:
            raise ValueError("GEMINI_MODEL is required")
        from google import genai
        from google.genai import types

        self._genai = genai
        self._keys_file = Path(api_keys_file).expanduser()
        if not self._keys_file.is_absolute():
            self._keys_file = Path.cwd() / self._keys_file
        self._keys_lock = threading.RLock()
        self._generate_lock = threading.Lock()
        self._api_keys = self._load_api_keys()
        self._client = genai.Client(api_key=self._api_keys[0])
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget
        self.retry_attempts = max(1, retry_attempts)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        try:
            normalized_thinking_level = types.ThinkingLevel(thinking_level.strip().upper())
        except ValueError as exc:
            allowed_levels = ", ".join(level.value for level in types.ThinkingLevel)
            raise ValueError(
                f"Invalid thinking level {thinking_level!r}; expected one of: {allowed_levels}"
            ) from exc
        generation_config = {}
        if model.startswith("gemini-3"):
            generation_config["thinking_config"] = types.ThinkingConfig(
                thinking_level=normalized_thinking_level
            )
        else:
            generation_config["temperature"] = 0.2
            generation_config["thinking_config"] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        self.generation_config = types.GenerateContentConfig(**generation_config)
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        with self._generate_lock:
            last_error: Exception | None = None
            for _ in range(len(self._api_keys)):
                for attempt in range(self.retry_attempts):
                    try:
                        response = self._client.models.generate_content(
                            model=self.model, contents=prompt, config=self.generation_config
                        )
                        usage = getattr(response, "usage_metadata", None)
                        self.last_usage = {
                            key: int(value)
                            for key in (
                                "prompt_token_count", "candidates_token_count", "thoughts_token_count",
                                "cached_content_token_count", "tool_use_prompt_token_count", "total_token_count",
                            )
                            if (value := getattr(usage, key, None)) is not None
                        }
                        text = getattr(response, "text", None)
                        if not text:
                            raise RuntimeError("The LLM returned an empty response")
                        return text.strip()
                    except Exception as exc:
                        last_error = exc
                        if self._is_rotatable_key_error(exc):
                            break
                        if attempt + 1 < self.retry_attempts:
                            time.sleep(self.retry_backoff_seconds * (2 ** attempt))
                        else:
                            raise
                if last_error is not None and self._is_rotatable_key_error(last_error):
                    if len(self._api_keys) == 1:
                        raise last_error
                    self._rotate_key()
            raise RuntimeError("All Gemini API keys failed") from last_error

    def _load_api_keys(self) -> list[str]:
        if not self._keys_file.is_file():
            raise FileNotFoundError(f"Gemini API key file not found: {self._keys_file}")
        keys = [line.strip() for line in self._keys_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")]
        if not keys:
            raise ValueError(f"No Gemini API keys found in: {self._keys_file}")
        return keys

    def _rotate_key(self) -> None:
        with self._keys_lock:
            failed_key = self._api_keys.pop(0)
            self._api_keys.append(failed_key)
            self._client = self._genai.Client(api_key=self._api_keys[0])

    @staticmethod
    def _is_rotatable_key_error(error: Exception) -> bool:
        status_code = getattr(error, "status_code", None)
        message = str(error).upper()
        return status_code in {401, 403} or any(marker in message for marker in (
            "API_KEY_INVALID", "INVALID API KEY", "UNAUTHENTICATED", "PERMISSION_DENIED",
            "KEY HAS EXPIRED", "KEY IS EXPIRED", "KEY HAS BEEN REVOKED",
        ))


class OpenRouterTextGenerator:
    def __init__(self, api_key: str, model: str, max_tokens: int | None = None,
                 reasoning_enabled: bool = True, timeout_seconds: int = 180) -> None:
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        if not model:
            raise ValueError("OPENROUTER_MODEL is required")
        self.api_key, self.model = api_key, model
        self.max_tokens = max_tokens
        self.reasoning_enabled = reasoning_enabled
        self.timeout_seconds = timeout_seconds
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "reasoning": {"enabled": self.reasoning_enabled},
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload, timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage") or {}
        self.last_usage = {
            "prompt_token_count": int(usage.get("prompt_tokens", 0) or 0),
            "candidates_token_count": int(usage.get("completion_tokens", 0) or 0),
            "total_token_count": int(usage.get("total_tokens", 0) or 0),
        }
        choices = body.get("choices") or []
        text = ((choices[0].get("message") if choices else None) or {}).get("content", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("OpenRouter returned an empty response")
        return text.strip()


class OllamaTextGenerator:
    def __init__(self, model: str = "qwen2.5:14b-instruct", host: str = "http://localhost:11434",
                 timeout_seconds: int = 300) -> None:
        self.model, self.host = model, host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.last_usage: dict[str, int] = {}

    def load(self) -> None:
        response = requests.post(f"{self.host}/api/generate", json={"model": self.model, "keep_alive": -1},
                                 timeout=self.timeout_seconds)
        response.raise_for_status()

    def generate(self, prompt: str) -> str:
        response = requests.post(f"{self.host}/api/chat", json={
            "model": self.model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "keep_alive": -1, "options": {"temperature": 0.1},
        }, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        prompt_tokens = int(payload.get("prompt_eval_count", 0) or 0)
        output_tokens = int(payload.get("eval_count", 0) or 0)
        self.last_usage = {"prompt_token_count": prompt_tokens, "candidates_token_count": output_tokens,
                           "total_token_count": prompt_tokens + output_tokens}
        text = (payload.get("message") or {}).get("content", "")
        if not text:
            raise RuntimeError("Ollama returned an empty response")
        return text.strip()

"""Replaceable text-generation adapters for the Telegram answer service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import requests


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate text from a complete prompt."""


class CallableTextGenerator:
    """Adapter for any local function or callable LLM client."""

    def __init__(self, function: Callable[[str], str]) -> None:
        self.function = function
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        return self.function(prompt)


class GeminiTextGenerator:
    """Gemini adapter using the official Google GenAI Python SDK."""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_output_tokens: int | None = None,
        thinking_budget: int = 0,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        if not model:
            raise ValueError("GEMINI_MODEL is required")
        from google import genai
        from google.genai import types

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget
        generation_config = {
            "temperature": 0.2,
            "thinking_config": types.ThinkingConfig(thinking_budget=thinking_budget),
        }
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        self.generation_config = types.GenerateContentConfig(**generation_config)
        self.last_usage: dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self.generation_config,
        )
        usage = getattr(response, "usage_metadata", None)
        self.last_usage = {
            key: int(value)
            for key in (
                "prompt_token_count",
                "candidates_token_count",
                "thoughts_token_count",
                "cached_content_token_count",
                "tool_use_prompt_token_count",
                "total_token_count",
            )
            if (value := getattr(usage, key, None)) is not None
        }
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("The LLM returned an empty response")
        return text.strip()


class OllamaTextGenerator:
    """Ollama adapter using the local HTTP API."""

    def __init__(
        self,
        model: str = "qwen2.5:14b-instruct",
        host: str = "http://localhost:11434",
        timeout_seconds: int = 300,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.last_usage: dict[str, int] = {}

    def load(self) -> None:
        """Load the model into Ollama before the first Telegram question."""
        response = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "keep_alive": -1},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "keep_alive": -1,
                "options": {"temperature": 0.1},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        prompt_tokens = int(payload.get("prompt_eval_count", 0) or 0)
        output_tokens = int(payload.get("eval_count", 0) or 0)
        self.last_usage = {
            "prompt_token_count": prompt_tokens,
            "candidates_token_count": output_tokens,
            "total_token_count": prompt_tokens + output_tokens,
        }
        text = (payload.get("message") or {}).get("content", "")
        if not text:
            raise RuntimeError("Ollama returned an empty response")
        return text.strip()

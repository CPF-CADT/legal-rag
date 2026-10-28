"""Gemini API client wrapper."""

from pathlib import Path

from google import genai


class IncompleteResponseError(RuntimeError):
    """Raised when Gemini did not produce a complete usable response."""


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def extract_chunk(self, chunk_path: Path, prompt: str) -> tuple[str, dict]:
        uploaded = self.client.files.upload(file=str(chunk_path))
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded, prompt],
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError(f"Gemini returned empty text for {chunk_path}")

        candidates = getattr(response, "candidates", None) or []
        if candidates:
            finish_reason = getattr(candidates[0], "finish_reason", None)
            if finish_reason is not None and "STOP" not in str(finish_reason).upper():
                raise IncompleteResponseError(
                    f"Gemini returned an incomplete response ({finish_reason}) for {chunk_path}"
                )

        usage = response.usage_metadata
        token_usage = {
            "model": self.model,
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
            "thinking_tokens": getattr(usage, "thoughts_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
        }
        return text, token_usage

"""HTTP client for the FastAPI legal-answer endpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass(frozen=True)
class ApiAnswerResult:
    """Answer shape consumed by the Telegram formatter and logger."""

    answer: str | None
    sources: list[dict[str, Any]] = field(default_factory=list)
    has_sufficient_evidence: bool = False
    usage: dict[str, int] = field(default_factory=dict)
    retrieved_context: str = ""


class LegalRagApiClient:
    """Call the internal FastAPI service without loading retrieval locally."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    def answer(self, question: str, *, top_k: int = 5) -> ApiAnswerResult:
        try:
            response = httpx.post(
                f"{self.base_url}/api/summarize",
                json={"query": question, "top_k": top_k},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise RuntimeError("LegalRAG API is unavailable") from exc

        if response.is_error:
            detail = "LegalRAG API request failed"
            try:
                detail = response.json().get("error", {}).get("message", detail)
            except (TypeError, ValueError):
                pass
            raise RuntimeError(detail)

        payload = response.json()
        return ApiAnswerResult(
            answer=payload.get("summary"),
            sources=payload.get("sources", []),
            has_sufficient_evidence=bool(payload.get("has_sufficient_evidence", False)),
        )

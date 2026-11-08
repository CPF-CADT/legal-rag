"""Framework-independent domain contracts and DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class RetrievalUnavailableError(RuntimeError):
    """The retrieval index or model is unavailable."""


class LLMUnavailableError(RuntimeError):
    """The configured text generation service is unavailable."""


class RetrieverPort(Protocol):
    def load(self) -> None: ...
    def search(self, query: str, *, candidate_count: int, top_k: int) -> list[dict[str, Any]]: ...
    def filter_options(self) -> dict[str, list[str]]: ...


class AnswerPort(Protocol):
    def answer(self, question: str, *, top_k: int) -> "SummaryResult": ...


@dataclass(frozen=True)
class SummaryResult:
    answer: str | None
    sources: list[dict[str, Any]] = field(default_factory=list)
    has_sufficient_evidence: bool = False

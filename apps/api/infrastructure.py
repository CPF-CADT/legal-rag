"""Adapters around the existing LegalRAG retriever and answer service."""

from __future__ import annotations

import threading
from typing import Any

from .config import Settings
from .domain import LLMUnavailableError, RetrievalUnavailableError, SummaryResult


class RetrieverAdapter:
    """Expose complete article records from the configured production retriever."""

    def __init__(self, retriever: Any) -> None:
        self.retriever = retriever

    def load(self) -> None:
        try:
            self.retriever.load()
        except Exception as exc:
            raise RetrievalUnavailableError("retrieval dependencies are unavailable") from exc

    def search(self, query: str, *, candidate_count: int, top_k: int) -> list[dict[str, Any]]:
        try:
            results = self.retriever.search(query, candidate_count=candidate_count, top_k=top_k)
            return [
                {**result, "article_text": result.get("article_text", result.get("answer_context", ""))}
                for result in results
            ]
        except Exception as exc:
            raise RetrievalUnavailableError("retrieval failed") from exc

    def filter_options(self) -> dict[str, list[str]]:
        try:
            return self.retriever.filter_options()
        except Exception as exc:
            raise RetrievalUnavailableError("filter options unavailable") from exc


class AnswerServiceAdapter:
    """Translate the existing AnswerService contract into the domain port."""

    def __init__(self, service: Any) -> None:
        self.service = service
        self._lock = threading.Lock()

    def answer(self, question: str, *, top_k: int) -> SummaryResult:
        try:
            with self._lock:
                result = self.service.answer(question, top_k=top_k)
            sources = [self._with_article_text(source) for source in result.sources]
            return SummaryResult(
                answer=result.answer if result.has_sufficient_evidence else None,
                sources=sources if result.has_sufficient_evidence else [],
                has_sufficient_evidence=result.has_sufficient_evidence,
            )
        except Exception as exc:
            try:
                from answer_service import AnswerGenerationError
            except ImportError:
                AnswerGenerationError = ()
            if AnswerGenerationError and isinstance(exc, AnswerGenerationError):
                raise LLMUnavailableError("summary generation failed") from exc
            raise RetrievalUnavailableError("retrieval failed during summarization") from exc

    def _with_article_text(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            **result,
            "article_text": result.get("article_text", result.get("answer_context", "")),
        }


def build_runtime(settings: Settings) -> tuple[RetrieverAdapter, AnswerServiceAdapter]:
    """Build the production adapters without importing heavy dependencies at module load."""
    from runtime_factory import build_runtime_services

    services = build_runtime_services(
        settings.project_root,
        candidate_count=settings.candidate_count,
        top_k=settings.default_top_k,
        min_similarity=settings.min_similarity,
    )
    return RetrieverAdapter(services.retriever), AnswerServiceAdapter(services.answer_service)

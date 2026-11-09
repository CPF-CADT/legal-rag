"""Use cases for search and grounded summarization."""

from __future__ import annotations

from typing import Any

from .config import Settings
from apps.api.domain import AnswerPort, RetrieverPort
from .schemas import MatchedChunk, SearchFilters, SearchItem, SearchResponse, SummarizeResponse


def to_search_item(result: dict[str, Any]) -> SearchItem:
    return SearchItem(
        rank=int(result.get("rank", 0)),
        article_id=str(result.get("article_id", "")),
        document_id=str(result.get("document_id", "")),
        publication_date=str(result.get("publication_date", "")),
        title=str(result.get("title", "")),
        article_number=str(result.get("article_number", "")),
        chapter_number=str(result.get("chapter_number", "")),
        chapter_title=str(result.get("chapter_title", "")),
        article_text=str(result.get("article_text", "")),
        source_url=str(result.get("source_url", "")),
        pdf_url=str(result.get("pdf_url", "")),
        score=float(result.get("best_similarity", 0.0)),
        matched_chunks=[
            MatchedChunk(
                chunk_id=str(chunk.get("chunk_id", "")),
                text=str(chunk.get("text", "")),
                similarity=float(chunk.get("similarity", 0.0)),
            )
            for chunk in result.get("matched_chunks", [])
        ],
    )


class SearchService:
    def __init__(self, retriever: RetrieverPort, settings: Settings) -> None:
        self.retriever = retriever
        self.settings = settings

    def search(self, query: str, top_k: int, filters: SearchFilters | None = None) -> SearchResponse:
        candidate_count = max(self.settings.candidate_count, top_k)
        results = self.retriever.search(
            query,
            candidate_count=candidate_count,
            top_k=candidate_count if filters else top_k,
        )
        if filters:
            results = [result for result in results if self._matches_filters(result, filters)]
        results = results[:top_k]
        items = [to_search_item(result) for result in results]
        return SearchResponse(query=query, items=items, count=len(items))

    @staticmethod
    def _matches_filters(result: dict[str, Any], filters: SearchFilters) -> bool:
        checks = (
            (filters.title, result.get("title", "")),
            (filters.chapter_number, result.get("chapter_number", "")),
            (filters.article_number, result.get("article_number", "")),
        )
        return all(not expected or str(actual).strip() == expected.strip() for expected, actual in checks)


class SummarizeService:
    def __init__(self, answer_service: AnswerPort) -> None:
        self.answer_service = answer_service

    def summarize(self, query: str, top_k: int) -> SummarizeResponse:
        result = self.answer_service.answer(query, top_k=top_k)
        sources = [to_search_item(source) for source in result.sources]
        return SummarizeResponse(
            query=query,
            summary=result.answer,
            sources=sources,
            has_sufficient_evidence=result.has_sufficient_evidence,
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from apps.api.main import create_app
from apps.api.config import Settings
from apps.api.domain import SummaryResult


@dataclass
class FakeRetriever:
    should_fail: bool = False

    def load(self) -> None:
        return None

    def search(self, query: str, *, candidate_count: int, top_k: int) -> list[dict[str, Any]]:
        if self.should_fail:
            raise RuntimeError("index unavailable: /srv/legal-rag/chroma")
        return [
            {
                "rank": 1,
                "article_id": "doc-1-article-7",
                "document_id": "doc-1",
                "title": "Employment Law",
                "article_number": "7",
                "article_text": "COMPLETE ARTICLE BODY, including the non-matching paragraphs.",
                "source_url": "https://example.test/law/doc-1",
                "pdf_url": "https://example.test/law/doc-1.pdf",
                "best_similarity": 0.82,
                "matched_chunks": [],
                "local_pdf_path": "/srv/legal-rag/data/doc-1.pdf",
                "source_text_path": "/srv/legal-rag/data/doc-1.txt",
            }
        ][:top_k]


@dataclass
class FakeAnswerService:
    insufficient: bool = False
    should_fail: bool = False

    def answer(self, question: str, *, top_k: int) -> SummaryResult:
        if self.should_fail:
            raise RuntimeError("provider response included secret details")
        if self.insufficient:
            return SummaryResult(answer=None, sources=[], has_sufficient_evidence=False)
        return SummaryResult(
            answer="ចម្លើយសង្ខេបពីអត្ថបទច្បាប់ដែលបានរកឃើញ។",
            sources=[
                {
                    "article_id": "doc-1-article-7",
                    "document_id": "doc-1",
                    "title": "Employment Law",
                    "article_number": "7",
                    "article_text": "COMPLETE ARTICLE BODY, including the non-matching paragraphs.",
                    "source_url": "https://example.test/law/doc-1",
                    "pdf_url": "https://example.test/law/doc-1.pdf",
                    "best_similarity": 0.82,
                    "matched_chunks": [],
                }
            ],
            has_sufficient_evidence=True,
        )


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    retriever = FakeRetriever()
    answer_service = FakeAnswerService()
    app = create_app(
        Settings(project_root=Settings.from_environment().project_root),
        retriever=retriever,
        answer_service=answer_service,
    )
    with TestClient(app) as test_client:
        yield test_client, retriever, answer_service

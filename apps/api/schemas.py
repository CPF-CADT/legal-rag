"""Public HTTP request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SearchFilters(BaseModel):
    title: str | None = None
    chapter_number: str | None = None
    article_number: str | None = None


class QueryRequest(BaseModel):
    query: str = Field(..., max_length=4000, description="A legal question in Khmer")
    top_k: int = Field(5, ge=1, le=20)
    filters: SearchFilters | None = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


class MatchedChunk(BaseModel):
    chunk_id: str
    text: str
    similarity: float


class SearchItem(BaseModel):
    rank: int
    article_id: str
    document_id: str
    publication_date: str
    title: str
    article_number: str
    chapter_number: str
    chapter_title: str
    article_text: str
    source_url: str
    pdf_url: str
    score: float
    matched_chunks: list[MatchedChunk] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    items: list[SearchItem]
    count: int


class FilterOptionsResponse(BaseModel):
    titles: list[str]
    chapters: list[str]
    articles: list[str]


class SummarizeResponse(BaseModel):
    query: str
    summary: str | None
    sources: list[SearchItem]
    has_sufficient_evidence: bool


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str

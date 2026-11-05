"""Structure-preserving, token-aware chunking."""

from __future__ import annotations

import re
from typing import Any, Callable

from .config import PipelineConfig
from .io_utils import write_jsonl


def recursive_split(
    text: str, token_count: Callable[[str], int], budget: int, level: int = 0
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if token_count(text) <= budget:
        return [text]
    separators = [r"\n\n+", r"\n+", r"(?<=[។៕?!])\s+", r"\s+"]
    if level < len(separators):
        units = [part.strip() for part in re.split(separators[level], text) if part.strip()]
        if len(units) > 1:
            chunks: list[str] = []
            current = ""
            for unit in units:
                candidate = f"{current} {unit}".strip() if current else unit
                if current and token_count(candidate) > budget:
                    chunks.append(current)
                    current = unit
                else:
                    current = candidate
            if current:
                chunks.append(current)
            if all(token_count(chunk) <= budget for chunk in chunks):
                return chunks
            return [
                piece
                for chunk in chunks
                for piece in recursive_split(chunk, token_count, budget, level + 1)
            ]
        return recursive_split(text, token_count, budget, level + 1)

    chunks: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if current and token_count(candidate) > budget:
            chunks.append(current)
            current = character
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def build_chunks(articles: list[dict[str, Any]], config: PipelineConfig) -> list[dict[str, Any]]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    tokenizer.model_max_length = 10**9

    def token_count(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    chunks: list[dict[str, Any]] = []
    for article in articles:
        prefix = " | ".join(
            str(value)
            for value in [article.get("title"), article.get("article_number")]
            if value is not None and value != ""
        )
        budget = max(1, config.max_chunk_tokens - token_count(prefix))
        pieces = recursive_split(article["text"], token_count, budget)
        for index, piece in enumerate(pieces, start=1):
            chunks.append(
                {
                    "chunk_id": f"{article['article_id']}-chunk-{index}",
                    "article_id": article["article_id"],
                    "document_id": article["document_id"],
                    "article_number": article["article_number"],
                    "title": article["title"],
                    "domain": article.get("domain", ""),
                    "source_url": article["source_url"],
                    "pdf_url": article["pdf_url"],
                    "chunk_index": index,
                    "chunk_count": len(pieces),
                    "text": piece,
                    "search_text": f"{prefix}\n{piece}".strip(),
                }
            )
    write_jsonl(config.chunk_path, chunks)
    return chunks

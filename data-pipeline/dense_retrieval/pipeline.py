"""End-to-end orchestration."""

from __future__ import annotations

from typing import Any

from .chroma_index import build_index
from .chunking import build_chunks
from .config import PipelineConfig
from .embeddings import embed_chunks
from .prepare_articles import prepare_articles


def run_pipeline(config: PipelineConfig) -> dict[str, Any]:
    config.create_output_dirs()
    articles = prepare_articles(config)
    chunks = build_chunks(articles, config)
    vectors = embed_chunks(chunks, config)
    index = build_index(chunks, vectors, config)
    return {
        "articles": len(articles),
        "chunks": len(chunks),
        "embedding_shape": list(vectors.shape),
        "index": index,
    }

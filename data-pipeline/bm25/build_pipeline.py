"""Build the article/chunk artifacts and the BM25 index without embeddings."""

from __future__ import annotations

from pathlib import Path

from apps.core.retrieval_config import PipelineConfig
from dense_retrieval.chunking import build_chunks
from dense_retrieval.prepare_articles import prepare_articles

from .build_index import build_index


def build_bm25_pipeline(config: PipelineConfig | None = None) -> Path:
    """Prepare legal records and build the SQLite FTS5 BM25 index."""
    config = config or PipelineConfig(project_root=Path.cwd())
    config.create_output_dirs()
    articles = prepare_articles(config)
    chunks = build_chunks(articles, config)
    index_path = build_index(config)
    print(f"Prepared articles: {len(articles)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Built BM25 index: {index_path}")
    return index_path


if __name__ == "__main__":
    build_bm25_pipeline()

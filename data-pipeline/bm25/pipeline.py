"""Build the article-level BM25 pipeline without embeddings or chunking."""

from __future__ import annotations

from pathlib import Path

from apps.core.retrieval_config import PipelineConfig
from .sqlite_index import build_index


def build_bm25_pipeline(config: PipelineConfig | None = None) -> Path:
    """Build the SQLite FTS5 BM25 index from prepared articles.jsonl."""
    config = config or PipelineConfig(project_root=Path.cwd())
    config.create_output_dirs()
    index_path = build_index(config)
    print(f"Indexed articles: {sum(1 for _ in config.article_path.open(encoding='utf-8'))}")
    print(f"Built BM25 index: {index_path}")
    return index_path


if __name__ == "__main__":
    build_bm25_pipeline()

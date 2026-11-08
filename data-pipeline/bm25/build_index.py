"""Build the production SQLite FTS5 BM25 index from existing chunks."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from apps.core.retrieval_config import PipelineConfig

from apps.core.bm25.constants import BM25_VERSION, TOKENIZER_VERSION
from apps.core.bm25.tokenizer import indexable_chunk_text, tokenize


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_index(config: PipelineConfig | None = None) -> Path:
    config = config or PipelineConfig(project_root=Path.cwd())
    if not config.chunk_path.exists() or not config.article_path.exists():
        raise FileNotFoundError("Both chunks.jsonl and articles.jsonl are required")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = config.bm25_path.with_suffix(".sqlite3.tmp")
    if temporary_path.exists():
        temporary_path.unlink()
    connection = sqlite3.connect(temporary_path)
    try:
        connection.executescript(
            """
            CREATE TABLE index_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE documents (
                row_id INTEGER PRIMARY KEY,
                chunk_id TEXT NOT NULL UNIQUE,
                article_id TEXT NOT NULL,
                text TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                tokens,
                content='documents',
                content_rowid='row_id',
                tokenize='unicode61'
            );
            """
        )
        document_count = 0
        with config.chunk_path.open(encoding="utf-8") as stream:
            for row_id, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                chunk = json.loads(line)
                connection.execute(
                    "INSERT INTO documents(row_id, chunk_id, article_id, text) VALUES (?, ?, ?, ?)",
                    (row_id, str(chunk["chunk_id"]), str(chunk["article_id"]), str(chunk.get("text", ""))),
                )
                connection.execute(
                    "INSERT INTO documents_fts(rowid, tokens) VALUES (?, ?)",
                    (row_id, " ".join(tokenize(indexable_chunk_text(chunk)))),
                )
                document_count += 1
        metadata = {
            "bm25_version": BM25_VERSION,
            "tokenizer_version": TOKENIZER_VERSION,
            "chunks_sha256": sha256(config.chunk_path),
            "articles_sha256": sha256(config.article_path),
            "document_count": str(document_count),
            "k1": "1.5",
            "b": "0.75",
        }
        connection.executemany("INSERT INTO index_metadata(key, value) VALUES (?, ?)", metadata.items())
        connection.execute("INSERT INTO documents_fts(documents_fts) VALUES ('optimize')")
        connection.commit()
    finally:
        connection.close()
    os.replace(temporary_path, config.bm25_path)
    return config.bm25_path


if __name__ == "__main__":
    print(build_index())

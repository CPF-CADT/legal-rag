"""Read-only production BM25 retriever backed by SQLite FTS5."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from apps.core.retrieval_config import PipelineConfig
from apps.core.shared.query_correction import correct_query

from .constants import BM25_VERSION, TOKENIZER_VERSION
from .tokenizer import tokenize


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class BM25Retriever:
    def __init__(self, project_root: Path, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(project_root=project_root)
        self._connection: sqlite3.Connection | None = None
        self._articles: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def load(self) -> None:
        if self._connection is not None:
            return
        if not self.config.bm25_path.exists():
            raise FileNotFoundError(f"BM25 index not found: {self.config.bm25_path}. Run bm25.build_index first.")
        connection = sqlite3.connect(
            f"file:{self.config.bm25_path}?mode=ro", uri=True, check_same_thread=False
        )
        metadata = dict(connection.execute("SELECT key, value FROM index_metadata"))
        if metadata.get("bm25_version") != BM25_VERSION or metadata.get("tokenizer_version") != TOKENIZER_VERSION:
            connection.close()
            raise RuntimeError("BM25 index version is incompatible with the running code")
        if metadata.get("chunks_sha256") != sha256(self.config.chunk_path) or metadata.get("articles_sha256") != sha256(self.config.article_path):
            connection.close()
            raise RuntimeError("BM25 index is stale; rebuild it from the current corpus")
        self._connection = connection
        self._filtered_terms = {
            str(row[0]) for row in connection.execute("SELECT term FROM filtered_terms")
        }
        self._articles = {
            str(article["article_id"]): article
            for article in (
                json.loads(line)
                for line in self.config.article_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }

    def search(self, query: str, *, candidate_count: int = 100, top_k: int = 5) -> list[dict[str, Any]]:
        self.load()
        assert self._connection is not None
        candidates: dict[str, dict[str, Any]] = {}
        limit = max(candidate_count * 3, top_k * 5)
        for variant in correct_query(query).variants:
            tokens = [token for token in tokenize(variant) if token not in self._filtered_terms]
            if not tokens:
                continue
            match_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
            with self._lock:
                rows = self._connection.execute(
                    """
                    SELECT documents.chunk_id, documents.article_id, documents.text, bm25(documents_fts) AS rank_score
                    FROM documents_fts
                    JOIN documents ON documents.row_id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                    ORDER BY rank_score
                    LIMIT ?
                    """,
                    (match_query, limit),
                ).fetchall()
            for row in rows:
                score = -float(row[3])
                current = candidates.setdefault(row[1], {"score": float("-inf"), "matches": {}})
                current["score"] = max(current["score"], score)
                current["matches"][row[0]] = {"chunk_id": row[0], "text": row[2], "score": score}

        ranked = sorted(candidates.items(), key=lambda item: item[1]["score"], reverse=True)[:top_k]
        scores = [result["score"] for _, result in ranked]
        minimum, maximum = min(scores, default=0.0), max(scores, default=0.0)
        output = []
        for rank, (article_id, result) in enumerate(ranked, start=1):
            article = self._articles.get(article_id, {})
            normalized = 1.0 if maximum == minimum else (result["score"] - minimum) / (maximum - minimum)
            output.append({
                "rank": rank,
                "article_id": article_id,
                "title": article.get("title", ""),
                "article_number": article.get("article_number", ""),
                "chapter_number": article.get("chapter_number", "") or "",
                "chapter_title": article.get("chapter_title", "") or "",
                "document_id": article.get("document_id", ""),
                "answer_context": article.get("text", ""),
                "article_text": article.get("text", ""),
                "best_similarity": normalized,
                "bm25_score": result["score"],
                "matched_chunks": sorted(result["matches"].values(), key=lambda item: item["score"], reverse=True)[:2],
                "source_url": article.get("source_url", ""),
                "pdf_url": article.get("pdf_url", ""),
                "retrieval_method": "bm25",
            })
        return output

    def filter_options(self) -> dict[str, list[str]]:
        self.load()
        return {
            "titles": sorted({str(article.get("title", "")).strip() for article in self._articles.values() if article.get("title")}),
            "chapters": sorted({str(article.get("chapter_number", "")).strip() for article in self._articles.values() if article.get("chapter_number")}),
            "articles": sorted({str(article.get("article_number", "")).strip() for article in self._articles.values() if article.get("article_number")}),
        }

    @staticmethod
    def format_context(results: list[dict[str, Any]]) -> str:
        sections = []
        for result in results:
            sections.append("\n".join([
                f"ប្រភព {result['rank']}: {result['title']}",
                f"មាត្រា: {result['article_number']}",
                result["answer_context"],
            ]))
        return "\n\n---\n\n".join(sections)

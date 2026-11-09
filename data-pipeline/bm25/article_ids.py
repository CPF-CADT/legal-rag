"""Stable article-level identifiers shared by the BM25 builder and reader."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any


def base_article_id(article: dict[str, Any]) -> str:
    document_id = re.sub(r"\s+", "-", str(article.get("document_id", "")).strip())
    article_number = str(article.get("article_number", "")).strip()
    return f"{document_id}-{article_number}" if article_number else str(article["article_id"])


def assign_article_ids(articles: list[dict[str, Any]]) -> list[str]:
    totals = Counter(base_article_id(article) for article in articles)
    seen: Counter[str] = Counter()
    assigned = []
    for article in articles:
        base = base_article_id(article)
        seen[base] += 1
        assigned.append(base if totals[base] == 1 else f"{base}-{seen[base]}")
    return assigned

"""Evaluate BM25 against manually judged article IDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.core.bm25.sqlite_retriever import BM25Retriever


def evaluate(retriever: BM25Retriever, cases: list[dict[str, Any]], k: int = 5) -> dict[str, float]:
    judged = [case for case in cases if case.get("relevant_articles")]
    if not judged:
        return {"queries": 0.0, "recall_at_k": 0.0, "mrr": 0.0}

    hit_at_3 = 0.0
    hit_at_5 = 0.0
    recall_at_k = 0.0
    reciprocal_rank = 0.0
    for case in judged:
        relevant = set(case["relevant_articles"])
        results = retriever.search(case["query"], candidate_count=max(50, k), top_k=k)
        ranked = [
            f"{result['document_id']}-{result['article_number']}"
            for result in results
        ]
        ranks = [rank + 1 for rank, article_id in enumerate(ranked) if article_id in relevant]
        first = min(ranks, default=None)
        hit_at_3 += float(first is not None and first <= 3)
        hit_at_5 += float(first is not None and first <= 5)
        recall_at_k += len(set(ranked[:k]) & relevant) / len(relevant)
        reciprocal_rank += 1.0 / first if first is not None and first <= 3 else 0.0

    count = float(len(judged))
    return {
        "queries": count,
        "hit_at_3": hit_at_3 / count,
        "hit_at_5": hit_at_5 / count,
        "recall_at_k": recall_at_k / count,
        "mrr_at_3": reciprocal_rank / count,
    }


if __name__ == "__main__":
    root = Path.cwd()
    cases = json.loads((root / "experiments/evaluation/bm25_queries.json").read_text(encoding="utf-8"))
    retriever = BM25Retriever(root)
    print(json.dumps(evaluate(retriever, cases), ensure_ascii=False, indent=2))

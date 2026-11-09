"""Measure dictionary phrase and token coverage in the article corpus."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "data-pipeline"))

from apps.core.shared.normalization import normalize_khmer


def normalize_for_match(value: object) -> str:
    text = normalize_khmer(value)
    return re.sub(r"\s+", " ", text).strip()


def load_dictionary(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Dictionary must be a JSON list")
    return [
        item for item in data
        if isinstance(item, dict) and str(item.get("word", "")).strip()
    ]


def load_articles(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=PROJECT_ROOT / "experiments/evaluation/resources/khmer_khmer_dictionary.json",
    )
    parser.add_argument(
        "--articles",
        type=Path,
        default=PROJECT_ROOT / "data/dense_retrieval/articles.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/evaluation/dictionary_article_coverage.json",
    )
    args = parser.parse_args()

    dictionary = load_dictionary(args.dictionary)
    articles = load_articles(args.articles)
    corpus = []
    for article in articles:
        text = "\n".join(
            str(article.get(field, ""))
            for field in ("title", "chapter_title", "text", "search_text")
        )
        corpus.append(normalize_for_match(text))

    rows = []
    for item in dictionary:
        phrase = normalize_for_match(item["word"])
        parts = [part for part in phrase.split(" ") if part]
        phrase_df = sum(phrase in document for document in corpus)
        phrase_occurrences = sum(document.count(phrase) for document in corpus)
        part_rows = []
        for part in dict.fromkeys(parts):
            part_df = sum(part in document for document in corpus)
            part_occurrences = sum(document.count(part) for document in corpus)
            part_rows.append({
                "word": part,
                "document_frequency": part_df,
                "occurrences": part_occurrences,
                "appears": part_df > 0,
            })
        rows.append({
            "dictionary_id": str(item.get("id", "")),
            "word": phrase,
            "has_space": len(parts) > 1,
            "split_words": parts,
            "phrase_document_frequency": phrase_df,
            "phrase_occurrences": phrase_occurrences,
            "phrase_appears": phrase_df > 0,
            "all_split_words_appear": bool(parts) and all(row["appears"] for row in part_rows),
            "split_word_matches": part_rows,
        })

    summary = {
        "dictionary_path": str(args.dictionary),
        "articles_path": str(args.articles),
        "dictionary_entries": len(rows),
        "articles": len(articles),
        "multiword_entries": sum(row["has_space"] for row in rows),
        "phrases_appearing": sum(row["phrase_appears"] for row in rows),
        "phrases_not_appearing": sum(not row["phrase_appears"] for row in rows),
        "multiword_all_parts_appearing": sum(
            row["has_space"] and row["all_split_words_appear"] for row in rows
        ),
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, ensure_ascii=False, indent=2))
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()

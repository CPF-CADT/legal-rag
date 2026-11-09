"""Compare article-level JSON inverted indexes with and without the legal dictionary.

Outputs are written to data/evaluation/json_inverted_index_experiment/.
The JSON index is intentionally readable: terms map to document postings, and
documents map article IDs to source metadata.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data-pipeline"))

from bm25.article_ids import assign_article_ids
from bm25.tokenizer import TOKEN_RE, _segmenter, _stopwords
from apps.core.shared.normalization import normalize_khmer

ARTICLES = ROOT / "data/dense_retrieval/articles.jsonl"
DICTIONARY = ROOT / "experiments/evaluation/resources/law_word_term.json"
QUERIES = ROOT / "experiments/evaluation/bm25_queries.json"
OUTPUT = ROOT / "data/evaluation/json_inverted_index_experiment"


def load_articles() -> list[dict[str, object]]:
    return [json.loads(line) for line in ARTICLES.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_dictionary() -> list[tuple[str, str]]:
    records = json.loads(DICTIONARY.read_text(encoding="utf-8"))
    terms = {
        normalize_khmer(item["name"]): re.sub(r"\s+", "", normalize_khmer(item["name"]))
        for item in records
        if item.get("name")
    }
    return sorted(terms.items(), key=lambda item: len(item[0]), reverse=True)


def article_text(article: dict[str, object]) -> str:
    return " ".join(
        str(article.get(field, ""))
        for field in ("title", "article_number", "chapter_number", "chapter_title", "text")
        if article.get(field)
    )


def placeholder_name(index: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    value = index + 1
    encoded = ""
    while value:
        value, remainder = divmod(value - 1, len(letters))
        encoded = letters[remainder] + encoded
    return f"LAWTERM{encoded}TOKEN"


def tokenize_variant(text: str, dictionary_terms: list[tuple[str, str]] | None) -> list[str]:
    normalized = normalize_khmer(text)
    placeholders: dict[str, str] = {}
    if dictionary_terms:
        for index, (phrase, compact) in enumerate(dictionary_terms):
            if phrase in normalized:
                placeholder = placeholder_name(index)
                normalized = normalized.replace(phrase, f" {placeholder} ")
                placeholders[placeholder.casefold()] = compact.casefold()
    try:
        pieces = _segmenter()(normalized)
    except Exception:
        pieces = normalized.split()
    stopwords = _stopwords()
    terms: list[str] = []
    for piece in pieces:
        for term in TOKEN_RE.findall(piece):
            key = term.casefold()
            if key in placeholders:
                terms.append(placeholders[key])
            elif key and key not in stopwords and len(key) > 1:
                terms.append(key)
    return terms


def build_index(name: str, articles: list[dict[str, object]], dictionary_terms: list[tuple[str, str]] | None) -> dict[str, object]:
    article_ids = assign_article_ids(articles)
    documents: dict[str, dict[str, object]] = {}
    postings: dict[str, dict[str, object]] = {}
    lengths: dict[str, int] = {}
    for article, article_id in zip(articles, article_ids):
        tokens = tokenize_variant(article_text(article), dictionary_terms)
        counts = Counter(tokens)
        lengths[article_id] = len(tokens)
        documents[article_id] = {
            "title": str(article.get("title", "")),
            "document_id": str(article.get("document_id", "")),
            "article_number": str(article.get("article_number", "")),
        }
        for term, frequency in counts.items():
            entry = postings.setdefault(term, {"df": 0, "postings": {}})
            entry["df"] += 1
            entry["postings"][article_id] = frequency
    index = {
        "format": "json-inverted-index-v1",
        "variant": name,
        "dictionary_enabled": dictionary_terms is not None,
        "document_count": len(documents),
        "vocabulary_size": len(postings),
        "documents": documents,
        "document_lengths": lengths,
        "terms": dict(sorted(postings.items())),
    }
    path = OUTPUT / f"{name}_inverted_index.json"
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"variant": name, "index": str(path), "documents": len(documents), "vocabulary": len(postings), "bytes": path.stat().st_size}


def search(index: dict[str, object], query: str, top_k: int = 10) -> list[tuple[str, float]]:
    dictionary_terms = load_dictionary() if index["dictionary_enabled"] else None
    terms = tokenize_variant(query, dictionary_terms)
    docs = index["documents"]
    lengths = index["document_lengths"]
    avg_len = sum(lengths.values()) / max(len(lengths), 1)
    scores: Counter[str] = Counter()
    for term in set(terms):
        entry = index["terms"].get(term)
        if not entry:
            continue
        df = entry["df"]
        idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
        for document_id, tf in entry["postings"].items():
            length = lengths[document_id]
            norm = tf + 1.5 * (1 - 0.75 + 0.75 * length / max(avg_len, 1))
            scores[document_id] += idf * (tf * 2.5) / norm
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]


def evaluate(index: dict[str, object], queries: list[dict[str, object]]) -> dict[str, float | int]:
    rows = []
    for item in queries:
        relevant = set(item.get("relevant_articles", []))
        retrieved = {doc_id for doc_id, _ in search(index, str(item["query"]))}
        tp = len(retrieved & relevant)
        precision = tp / 10
        recall = tp / len(relevant) if relevant else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append((precision, recall, f1))
    if not rows:
        return {"queries": 0, "precision_at_10": 0.0, "recall_at_10": 0.0, "f1": 0.0}
    return {
        "queries": len(rows),
        "precision_at_10": sum(row[0] for row in rows) / len(rows),
        "recall_at_10": sum(row[1] for row in rows) / len(rows),
        "f1": sum(row[2] for row in rows) / len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", help="Print the documents containing this term in both indexes")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    articles = load_articles()
    dictionary_terms = load_dictionary()
    indexes = {}
    report = {"corpus": str(ARTICLES), "dictionary_entries": len(dictionary_terms), "variants": []}
    for name, enabled in (("without_dictionary", False), ("with_dictionary", True)):
        build_index(name, articles, dictionary_terms if enabled else None)
        index = json.loads((OUTPUT / f"{name}_inverted_index.json").read_text(encoding="utf-8"))
        indexes[name] = index
        summary = {"variant": name, "documents": index["document_count"], "vocabulary": index["vocabulary_size"], "index_bytes": (OUTPUT / f"{name}_inverted_index.json").stat().st_size}
        if QUERIES.exists():
            queries = json.loads(QUERIES.read_text(encoding="utf-8"))
            summary["evaluation"] = evaluate(index, queries)
        report["variants"].append(summary)
    (OUTPUT / "comparison_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.term:
        inspection = {"term": args.term, "variants": {}}
        for name, index in indexes.items():
            terms = tokenize_variant(args.term, load_dictionary() if index["dictionary_enabled"] else None)
            inspection["variants"][name] = {term: index["terms"].get(term, {"df": 0, "postings": {}}) for term in terms}
        (OUTPUT / "term_inspection.json").write_text(json.dumps(inspection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(inspection, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

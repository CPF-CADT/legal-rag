"""Khmer tokenization used only by the BM25 index."""

from __future__ import annotations

import re
from functools import lru_cache

from apps.core.shared.normalization import normalize_khmer

TOKEN_RE = re.compile(r"[0-9A-Za-z\u1780-\u17FF]+")
SAFE_STOPWORDS = frozenset({"និង", "ឬ", "នេះ", "នោះ", "ជា", "នៃ", "ទៅ", "ពី"})
LEGAL_TERMS = frozenset({
    "មួកសុវត្ថិភាព", "ចរាចរណ៍ផ្លូវគោក", "បទល្មើស", "ទណ្ឌកម្ម", "កិច្ចសន្យា",
    "រដ្ឋធម្មនុញ្ញ", "សិទ្ធិមនុស្ស", "ការទទួលខុសត្រូវ", "តុលាការ", "បណ្ដឹង",
})


@lru_cache(maxsize=1)
def _segmenter():
    from khmer_segmenter import KhmerSegmenter

    return KhmerSegmenter()


def tokenize(text: str) -> list[str]:
    """Return normalized Khmer/Latin/number terms without changing source text."""
    normalized = normalize_khmer(text)
    try:
        pieces = _segmenter().segment(normalized)
    except Exception:
        pieces = normalized.split()
    terms: list[str] = []
    for piece in pieces:
        terms.extend(TOKEN_RE.findall(piece))
    normalized_terms = [term.casefold() for term in terms if term and term.casefold() not in SAFE_STOPWORDS]
    for legal_term in LEGAL_TERMS:
        if legal_term in normalized:
            normalized_terms.append(legal_term.casefold())
    return normalized_terms


def indexable_chunk_text(chunk: dict[str, object]) -> str:
    """Build one standard BM25 document from the existing chunk fields."""
    title = str(chunk.get("title", ""))
    article_number = str(chunk.get("article_number", ""))
    chapter_number = str(chunk.get("chapter_number", ""))
    chapter_title = str(chunk.get("chapter_title", ""))
    body = str(chunk.get("text", chunk.get("search_text", "")))
    return " ".join(value for value in (title, article_number, chapter_number, chapter_title, body) if value)

"""Khmer tokenization used only by the BM25 index."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from apps.core.shared.normalization import normalize_khmer

TOKEN_RE = re.compile(r"[0-9A-Za-z\u1780-\u17FF]+")
SAFE_STOPWORDS = frozenset({"និង", "ឬ", "នេះ", "នោះ", "ជា", "នៃ", "ទៅ", "ពី"})
PROTECTED_TOKENS = frozenset({"មិន", "ទេ", "គ្មាន", "ហាម"})
LEGAL_TERMS = frozenset({
    "មួកសុវត្ថិភាព", "ចរាចរណ៍ផ្លូវគោក", "បទល្មើស", "ទណ្ឌកម្ម", "កិច្ចសន្យា",
    "រដ្ឋធម្មនុញ្ញ", "សិទ្ធិមនុស្ស", "ការទទួលខុសត្រូវ", "តុលាការ", "បណ្ដឹង",
})


@lru_cache(maxsize=1)
def _kswv2_stopwords() -> frozenset[str]:
    path = Path(__file__).resolve().parents[3] / "data" / "stopwords" / "kswv2-core.txt"
    if not path.exists():
        raise FileNotFoundError(f"KSWv2 stopword file not found: {path}")
    return frozenset(
        unicodedata.normalize("NFC", line.strip().lstrip("\ufeff\u200b"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _is_numeric_token(token: str) -> bool:
    return bool(token) and all(unicodedata.category(character) == "Nd" for character in token)


def _is_punctuation_token(token: str) -> bool:
    return bool(token) and all(unicodedata.category(character)[0] in "PS" for character in token)


def is_protected_token(token: str) -> bool:
    key = token.casefold()
    return key in (PROTECTED_TOKENS | LEGAL_TERMS) or _is_numeric_token(key)


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
    stopwords = SAFE_STOPWORDS | _kswv2_stopwords()
    protected = PROTECTED_TOKENS | LEGAL_TERMS
    normalized_terms = []
    for term in terms:
        key = term.casefold()
        if not key:
            continue
        if _is_punctuation_token(key):
            continue
        if key in stopwords and key not in protected and not _is_numeric_token(key):
            continue
        normalized_terms.append(key)
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

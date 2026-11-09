"""Khmer tokenization used only by the BM25 index."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from apps.core.shared.normalization import normalize_khmer

TOKEN_RE = re.compile(r"[0-9A-Za-z\u1780-\u17FF]+")


def _is_punctuation_token(token: str) -> bool:
    return bool(token) and all(unicodedata.category(character)[0] in "PS" for character in token)


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    path = Path(__file__).with_name("stopword-candidate.txt")
    if not path.exists():
        return frozenset()
    values = {
        unicodedata.normalize("NFC", line.strip().lstrip("\ufeff\u200b"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return frozenset(values)


@lru_cache(maxsize=1)
def _segmenter():
    from khmernltk import word_tokenize

    return word_tokenize


def tokenize(text: str) -> list[str]:
    """Return normalized Khmer/Latin/number terms without changing source text."""
    normalized = normalize_khmer(text)
    try:
        pieces = _segmenter()(normalized)
    except Exception:
        pieces = normalized.split()
    terms: list[str] = []
    for piece in pieces:
        terms.extend(TOKEN_RE.findall(piece))
    stopwords = _stopwords()
    normalized_terms = []
    for term in terms:
        key = term.casefold()
        if not key:
            continue
        if _is_punctuation_token(key):
            continue
        if len(key) == 1:
            continue
        if key in stopwords:
            continue
        normalized_terms.append(key)
    return normalized_terms

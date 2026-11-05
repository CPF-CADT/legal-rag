"""Khmer Unicode normalization used before chunking and embedding."""
from __future__ import annotations

import re
import unicodedata
from .cleaning import ZERO_WIDTH

SPELLING_VARIANTS = {
    "សំលៀកបំពាក់": "សម្លៀកបំពាក់",
    "ចំរៀង": "ចម្រៀង",
    "ជ័យជម្នះ": "ជ័យជំនះ",
}

def normalize_khmer_cluster_order(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    clusters, current = [], ""
    for char in decomposed:
        if unicodedata.combining(char) == 0 and current:
            clusters.append(current)
            current = ""
        current += char
    if current:
        clusters.append(current)
    ordered = []
    for cluster in clusters:
        if len(cluster) > 1:
            cluster = cluster[0] + "".join(sorted(cluster[1:], key=unicodedata.combining))
        ordered.append(cluster)
    return unicodedata.normalize("NFC", "".join(ordered))

def normalize_khmer(value: object) -> str:
    text = normalize_khmer_cluster_order(str(value or ""))
    text = text.translate(str.maketrans("", "", ZERO_WIDTH)).replace("\u00a0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = re.sub(r"\n{2,}", "\n", "\n".join(x for x in lines if x))
    for source, target in SPELLING_VARIANTS.items():
        text = text.replace(source, target)
    return text

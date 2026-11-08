"""Khmer query normalization and conservative spelling-variant generation."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .normalization import normalize_khmer


# Curated legal-domain corrections are applied before the general-purpose
# spellchecker. This prevents a generic dictionary from choosing a plausible
# but legally wrong word, such as ចំបាប់ for ចបាប់.
LEGAL_CORRECTIONS = {
    "ចបាប់": "ច្បាប់",
    "រដធម្មនុញ្ញ": "រដ្ឋធម្មនុញ្ញ",
    "តុលាកា": "តុលាការ",
    "បទល្មើ": "បទល្មើស",
    "ព្រហ្មទន្ឌ": "ព្រហ្មទណ្ឌ",
    "ទន្ឌកម្ម": "ទណ្ឌកម្ម",
    "សិទិ្ធ": "សិទ្ធិ",
    "កាតពកិច្ច": "កាតព្វកិច្ច",
    "យុតិធម៌": "យុត្តិធម៌",
    "បណ្តឹង": "បណ្ដឹង",
    "កិចសន្យា": "កិច្ចសន្យា",
    "រដាភិបាល": "រដ្ឋាភិបាល",
    "ក្រសួ": "ក្រសួង",
    "អាជ្ញាធ": "អាជ្ញាធរ",
    "រដបាល": "រដ្ឋបាល",
    "មន្រ្តី": "មន្ត្រី",
    "ប្រជាធិបតេយ": "ប្រជាធិបតេយ្យ",
    "សាធារណ": "សាធារណៈ",
    "គោលនយោបា": "គោលនយោបាយ",
    "អនុវត": "អនុវត្ត",
    "ចរាចរ": "ចរាចរណ៍",
    "គ្រោះថ្នា": "គ្រោះថ្នាក់",
    "សុវត្តិភាព": "សុវត្ថិភាព",
    "គ្រឿងញៀ": "គ្រឿងញៀន",
    "បរិស្ថា": "បរិស្ថាន",
    "សង្គមកិច": "សង្គមកិច្ច",
    "សេដកិច្ច": "សេដ្ឋកិច្ច",
}


@dataclass(frozen=True)
class QueryCorrection:
    original: str
    normalized: str
    corrected: str
    suggestions: tuple[str, ...]

    @property
    def variants(self) -> tuple[str, ...]:
        """Return unique query forms, preserving the original search intent."""
        # Search the complete normalized query and the complete corrected
        # query. Individual word suggestions are metadata, not standalone
        # queries, because searching them could broaden a legal question.
        values = (self.normalized, self.corrected)
        return tuple(dict.fromkeys(value for value in values if value))


@lru_cache(maxsize=1)
def _segmenter():
    from khmer_segmenter import KhmerSegmenter

    return KhmerSegmenter()


def correct_query(query: str) -> QueryCorrection:
    """Normalize a query and produce conservative Khmer spelling variants.

    The original query is never overwritten. Retrieved results can use all
    variants so a bad correction cannot remove a valid legal match.
    """
    normalized = normalize_khmer(query).replace("\n", " ").strip()
    if not normalized:
        return QueryCorrection(query, "", "", ())

    corrected = normalized
    legal_replacements: list[tuple[str, str]] = []
    for source, target in sorted(LEGAL_CORRECTIONS.items(), key=lambda item: len(item[0]), reverse=True):
        if source in corrected:
            corrected = corrected.replace(source, target)
            legal_replacements.append((source, target))

    diagnostics = _segmenter().detect_typos(corrected)
    replacements: list[tuple[int, int, str]] = []
    suggestions: list[str] = [target for _, target in legal_replacements]
    for diagnostic in diagnostics:
        if not diagnostic.suggestions:
            continue
        suggestion = diagnostic.suggestions[0]
        suggestions.append(suggestion.text)
        replacements.append((diagnostic.start, diagnostic.end, suggestion.text))

    for start, end, replacement in sorted(replacements, reverse=True):
        corrected = corrected[:start] + replacement + corrected[end:]

    return QueryCorrection(
        original=query,
        normalized=normalized,
        corrected=corrected,
        suggestions=tuple(dict.fromkeys(suggestions)),
    )

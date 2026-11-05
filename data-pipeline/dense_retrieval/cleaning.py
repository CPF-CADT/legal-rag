"""Cleaning rules shared by offline indexing and server preparation."""
from __future__ import annotations

import re
import unicodedata

ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"
KHMER_DIGITS = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")
DECORATIVE_ONLY_RE = re.compile(r"^\s*(?:[•+\-–—·]+|\.{2,})\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*(?:[0-9០-៩]{3,}|[0-9០-៩]+\s*/\s*[0-9០-៩]+)\s*$")

def unicode_clean(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return text.translate(str.maketrans("", "", ZERO_WIDTH)).replace("\u00a0", " ")

def clean_line(value: object) -> str:
    line = unicode_clean(value).strip()
    if not line or DECORATIVE_ONLY_RE.fullmatch(line):
        return ""
    line = re.sub(r"\.{3,}", " ", line)
    return re.sub(r"[ \t]+", " ", line).strip()

def remove_page_number_lines(lines: list[str]) -> list[str]:
    result = []
    for index, item in enumerate(lines):
        line = unicode_clean(item).strip()
        if not PAGE_NUMBER_RE.fullmatch(line):
            result.append(item)
            continue
        previous = next((unicode_clean(lines[i]).strip() for i in range(index - 1, -1, -1) if unicode_clean(lines[i]).strip()), "")
        blank_before = index > 0 and not unicode_clean(lines[index - 1]).strip()
        blank_after = index + 1 < len(lines) and not unicode_clean(lines[index + 1]).strip()
        if not (previous and (previous.endswith(("។", "៕")) or blank_before or blank_after)):
            result.append(item)
    return result

def clean_multiline_text(lines: list[str]) -> str:
    cleaned = [clean_line(line) for line in remove_page_number_lines(lines)]
    return re.sub(r"\n{2,}", "\n", "\n".join(x for x in cleaned if x).strip())

def clean_title(value: object) -> str:
    return " ".join(clean_line(value).split())

def number_value(value: object) -> int | None:
    digits = unicode_clean(value).translate(KHMER_DIGITS)
    return int(digits) if digits.isdigit() else None

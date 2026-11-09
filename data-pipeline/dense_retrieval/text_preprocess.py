"""Article preparation, text cleaning, and chunking for dense retrieval."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Callable, Iterable

from apps.core.retrieval_config import PipelineConfig
from apps.core.shared.normalization import normalize_khmer

from apps.core.shared.cleaning import (
    clean_line,
    clean_multiline_text,
    clean_title,
    number_value,
    remove_page_number_lines,
    unicode_clean,
)

NUM = r"[0-9០-៩]+"
ARTICLE_WORD = r"(?:" + NUM + r"|មួយ|ពីរ|បី|បួន|ប្រាំ(?:មួយ|ពីរ|បី|បួន|ប្រាំ)?)"
CHAPTER_RE = re.compile(r"^\s*(?:ផ្នែក\s*[:：]\s*)?ជំពូក\s*ទី\s*(" + NUM + r")\s*(?:[._៖:-]+)?\s*(.*)$")
SECTION_RE = re.compile(r"^\s*ផ្នែក\s*ទី\s*(" + NUM + r")\s*(?:[._៖:-]+)?\s*(.*)$")
ARTICLE_RE = re.compile(r"^\s*[\"“”]?\s*មាត្រា\s*(" + ARTICLE_WORD + r")(?:\s|[._៖:-]|$)", re.I)
ARTICLE_MARKER_RE = re.compile(r"^\s*\[START_ARTICLE\s*:\s*(" + NUM + r")\s*\]\s*$")
APPENDIX_RE = re.compile(r"^\s*(?:ឧបសម្ព័ន្ធ|តារាង|ទម្រង់គំរូ|គំរូសំណើ|បញ្ជីឯកសារ|សេចក្តីបន្ថែម)")
CLOSING_RE = re.compile(r"^\s*(?:ធ្វើនៅ.*ថ្ងៃទី|រាជធានីភ្នំពេញ.*ថ្ងៃទី|ព្រះហស្តលេខា(?:\s|$))")
LEGAL_FOOTER_RE = re.compile(r"(?:ត្រូវប្រកាសជាការប្រញាប់|ធ្វើនៅព្រះបរមរាជវាំង)")


def _heading(pattern: re.Pattern[str], line: str):
    match = pattern.match(unicode_clean(line))
    return (number_value(match.group(1)), clean_title(match.group(2))) if match else None


def _article_number(value: str) -> int | str:
    number = number_value(value)
    return number if number is not None else value


def _remove_heading(lines: list[str]) -> list[str]:
    cleaned = [clean_line(x) for x in remove_page_number_lines(lines)]
    cleaned = [x for x in cleaned if x]
    if cleaned:
        cleaned[0] = re.sub(
            r'^\s*["“”]?\s*មាត្រា\s*' + ARTICLE_WORD + r'\s*(?:[._៖:-]+\s*)?',
            '', cleaned[0], count=1,
        ).strip()
        if not cleaned[0]:
            cleaned.pop(0)
    return cleaned


def parse_document(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse a legal source into preamble, article records, and chapters."""
    normalized = unicode_clean(text)
    normalized = re.sub(r"\[START_ARTICLE\s*:\s*(" + NUM + r")\s*\]", lambda m: f"\n[START_ARTICLE:{m.group(1)}]\n", normalized)
    if not ARTICLE_MARKER_RE.search(normalized):
        normalized = re.sub(
            r'(?m)^\s*(?=["“”]?\s*មាត្រា\s*(' + NUM + r')(?:\s|[._៖:-]|$))',
            lambda m: f"\n[START_ARTICLE:{m.group(1)}]\n", normalized,
        )
    lines = normalized.splitlines()
    preamble, articles, chapters = [], [], []
    chapter_number = chapter_title = section_number = section_title = None
    current = None
    appendix_started = False

    def save() -> None:
        nonlocal current
        if not current:
            return
        body_lines = _remove_heading(current["lines"])
        stop = next((i for i, line in enumerate(body_lines) if CLOSING_RE.match(line) or APPENDIX_RE.match(line) or LEGAL_FOOTER_RE.search(line)), None)
        if stop is not None:
            body_lines = body_lines[:stop]
        body = clean_multiline_text(body_lines)
        if body:
            articles.append({
                "article_number": current["article_number"],
                "text": body,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title or "",
                "section_number": section_number,
                "section_title": section_title or "",
            })
        current = None

    for raw_line in lines:
        if appendix_started:
            continue
        line = raw_line.strip()
        chapter = _heading(CHAPTER_RE, line)
        section = _heading(SECTION_RE, line)
        article = ARTICLE_RE.match(line)
        marker = ARTICLE_MARKER_RE.match(line)
        if current and (CLOSING_RE.match(line) or APPENDIX_RE.match(line) or LEGAL_FOOTER_RE.search(line)):
            save()
            appendix_started = True
            continue
        if marker:
            save()
            current = {"article_number": _article_number(marker.group(1)), "lines": []}
        elif article:
            save()
            current = {"article_number": _article_number(article.group(1)), "lines": []}
        elif chapter:
            save()
            chapter_number, chapter_title = chapter
            section_number = section_title = None
        elif section:
            save()
            if chapter_number is None:
                chapter_number = None
                chapter_title = ""
            section_number, section_title = section
        elif current:
            current["lines"].append(raw_line)
        elif line:
            preamble.append(raw_line)
    save()
    return clean_multiline_text(preamble), articles, chapters


def clean_text(value: Any) -> str:
    value = unicodedata.normalize("NFC", str(value or ""))
    value = value.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    return "\n".join(line.rstrip() for line in value.splitlines()).strip()


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def load_documents(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {
            str(row["document_id"]).strip(): row
            for row in csv.DictReader(stream)
            if row.get("document_id")
        }


def prepare_articles(
    config: PipelineConfig,
    ocr_paths: list[Path] | None = None,
    extra_articles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Parse OCR and core-law sources into normalized article records."""
    documents = load_documents(config.documents_csv)
    records: list[dict[str, Any]] = []
    paths = ocr_paths if ocr_paths is not None else list(config.ocr_dir.glob("*.txt"))
    for text_path in sorted(paths, key=lambda item: item.name):
        document_id = text_path.stem
        document = documents.get(document_id)
        if document is None:
            continue
        raw_text = text_path.read_text(encoding="utf-8-sig", errors="replace")
        preamble, articles, _chapters = parse_document(raw_text)
        if not articles:
            continue
        for index, article in enumerate(articles, start=1):
            text = normalize_khmer(article["text"])
            if not text:
                continue
            title = normalize_khmer(document.get("title", ""))
            article_number = article["article_number"]
            records.append({
                "article_id": f"{document_id}-article-{index}",
                "document_id": document_id,
                "article_number": article_number,
                "chapter_number": article.get("chapter_number"),
                "chapter_title": normalize_khmer(article.get("chapter_title", "")),
                "section_number": article.get("section_number"),
                "section_title": normalize_khmer(article.get("section_title", "")),
                "title": title,
                "document_type": normalize_khmer(document.get("document_type", "")),
                "domain": normalize_khmer(document.get("category", "")),
                "publication_date": document.get("publication_date", "") or document.get("publication_year", ""),
                "source_url": document.get("detail_url") or document.get("pdf_url", ""),
                "pdf_url": document.get("pdf_url", ""),
                "text_file": str(text_path),
                "preamble": normalize_khmer(preamble),
                "text": text,
                "search_text": normalize_khmer(f"{title}\n{article_number}\n{text}"),
                "normalization_version": "legal-cleaning-v1-khmer-normalization-v2",
            })
    records.extend(extra_articles or [])
    write_jsonl(config.article_path, records)
    return records


def recursive_split(
    text: str, token_count: Callable[[str], int], budget: int, level: int = 0
) -> list[str]:
    """Split text recursively while preserving legal structure where possible."""
    text = text.strip()
    if not text:
        return []
    if token_count(text) <= budget:
        return [text]
    separators = [r"\n\n+", r"\n+", r"(?<=[។៕?!])\s+", r"\s+"]
    if level < len(separators):
        units = [part.strip() for part in re.split(separators[level], text) if part.strip()]
        if len(units) > 1:
            chunks: list[str] = []
            current = ""
            for unit in units:
                candidate = f"{current} {unit}".strip() if current else unit
                if current and token_count(candidate) > budget:
                    chunks.append(current)
                    current = unit
                else:
                    current = candidate
            if current:
                chunks.append(current)
            if all(token_count(chunk) <= budget for chunk in chunks):
                return chunks
            return [piece for chunk in chunks for piece in recursive_split(chunk, token_count, budget, level + 1)]
        return recursive_split(text, token_count, budget, level + 1)
    chunks: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if current and token_count(candidate) > budget:
            chunks.append(current)
            current = character
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def build_chunks(articles: list[dict[str, Any]], config: PipelineConfig) -> list[dict[str, Any]]:
    """Create structure-preserving, token-aware embedding chunks."""
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    tokenizer.model_max_length = 10**9

    def token_count(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    chunks: list[dict[str, Any]] = []
    for article in articles:
        prefix = " | ".join(
            str(value)
            for value in [article.get("title"), article.get("article_number")]
            if value is not None and value != ""
        )
        budget = max(1, config.max_chunk_tokens - token_count(prefix))
        pieces = recursive_split(article["text"], token_count, budget)
        for index, piece in enumerate(pieces, start=1):
            chunks.append({
                "chunk_id": f"{article['article_id']}-chunk-{index}",
                "article_id": article["article_id"],
                "document_id": article["document_id"],
                "article_number": article["article_number"],
                "title": article["title"],
                "domain": article.get("domain", ""),
                "source_url": article["source_url"],
                "pdf_url": article["pdf_url"],
                "chunk_index": index,
                "chunk_count": len(pieces),
                "text": piece,
                "search_text": f"{prefix}\n{piece}".strip(),
            })
    write_jsonl(config.chunk_path, chunks)
    return chunks

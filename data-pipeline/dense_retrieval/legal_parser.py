"""Structure-aware parser matching the legal preprocessing notebook."""
from __future__ import annotations

import re
from typing import Any
from .cleaning import clean_line, clean_multiline_text, clean_title, number_value, remove_page_number_lines, unicode_clean

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
        cleaned[0] = re.sub(r'^\s*[\"“”]?\s*មាត្រា\s*' + ARTICLE_WORD + r'\s*(?:[._៖:-]+\s*)?', '', cleaned[0], count=1).strip()
        if not cleaned[0]:
            cleaned.pop(0)
    return cleaned

def parse_document(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    normalized = unicode_clean(text)
    normalized = re.sub(r"\[START_ARTICLE\s*:\s*(" + NUM + r")\s*\]", lambda m: f"\n[START_ARTICLE:{m.group(1)}]\n", normalized)
    if not ARTICLE_MARKER_RE.search(normalized):
        normalized = re.sub(r"(?m)^\s*(?=[\"“”]?\s*មាត្រា\s*(" + NUM + r")(?:\s|[._៖:-]|$))", lambda m: f"\n[START_ARTICLE:{m.group(1)}]\n", normalized)
    lines = normalized.splitlines()
    preamble, articles, chapters = [], [], []
    chapter_number = chapter_title = section_number = section_title = None
    current = None
    appendix_started = False

    def save():
        nonlocal current
        if not current:
            return
        body_lines = _remove_heading(current['lines'])
        stop = next((i for i, line in enumerate(body_lines) if CLOSING_RE.match(line) or APPENDIX_RE.match(line) or LEGAL_FOOTER_RE.search(line)), None)
        if stop is not None:
            body_lines = body_lines[:stop]
        body = clean_multiline_text(body_lines)
        if body:
            articles.append({
                'article_number': current['article_number'],
                'text': body,
                'chapter_number': chapter_number,
                'chapter_title': chapter_title or '',
                'section_number': section_number,
                'section_title': section_title or '',
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
            current = {'article_number': _article_number(marker.group(1)), 'lines': []}
        elif article:
            save()
            current = {'article_number': _article_number(article.group(1)), 'lines': []}
        elif chapter:
            save()
            chapter_number, chapter_title = chapter
            section_number = section_title = None
        elif section:
            save()
            if chapter_number is None:
                chapter_number = None
                chapter_title = ''
            section_number, section_title = section
        elif current:
            current['lines'].append(raw_line)
        elif line:
            preamble.append(raw_line)
    save()
    return clean_multiline_text(preamble), articles, chapters

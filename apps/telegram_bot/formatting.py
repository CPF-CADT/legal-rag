"""Convert legal answers to safe Telegram HTML."""

from __future__ import annotations

import html
import re
from typing import Any


def format_telegram_answer(result: Any) -> str:
    answer = sanitize_answer_html(result.answer or "សូមអភ័យទោស មិនមានចម្លើយគ្រប់គ្រាន់ពីឯកសារច្បាប់ទេ។")
    if not result.has_sufficient_evidence or not result.sources:
        return f"⚖️ {answer}"

    grouped_sources: dict[tuple[str, str], list[str]] = {}
    for source in result.sources:
        label = source.get("title") or source.get("document_id") or "ប្រភពច្បាប់"
        url = source.get("source_url") or source.get("pdf_url") or ""
        key = (label, url)
        grouped_sources.setdefault(key, [])
        article_number = format_article_number(source.get("article_number"))
        if article_number and article_number not in grouped_sources[key]:
            grouped_sources[key].append(article_number)

    source_lines = []
    for (label, url), article_numbers in grouped_sources.items():
        article_text = " ".join(article_numbers)
        source_label = f"{label} មាត្រា {article_text}" if article_text else label
        if url:
            source_lines.append(
                f'<a href="{html.escape(url, quote=True)}">{html.escape(source_label)}</a>'
            )
        else:
            source_lines.append(html.escape(source_label))

    return f"⚖️ {answer}\n\n<b>📚 ប្រភព៖</b>\n" + "\n".join(source_lines)


def split_telegram_html(message: str, max_length: int = 3800) -> list[str]:
    lines = message.splitlines()
    parts: list[str] = []
    current = ""
    for line in lines:
        candidate = line if not current else f"{current}\n{line}"
        if current and len(candidate) > max_length:
            parts.append(current)
            current = line
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts or [""]


def sanitize_answer_html(answer: str) -> str:
    lines = []
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        bullet = re.match(r"^[*+•-]\s+(.+)$", line)
        if heading:
            lines.append(f"<b>{markdown_inline_to_html(heading.group(1))}</b>")
        elif bullet:
            lines.append(f"• {markdown_inline_to_html(bullet.group(1))}")
        else:
            lines.append(markdown_inline_to_html(line))
    return "\n".join(lines)


def markdown_inline_to_html(value: str) -> str:
    safe = html.escape(value, quote=False)
    placeholders: dict[str, str] = {}

    def protect(match: re.Match[str]) -> str:
        key = f"\x00{len(placeholders)}\x00"
        placeholders[key] = f"<code>{match.group(1)}</code>"
        return key

    safe = re.sub(r"`([^`\n]+)`", protect, safe)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"__(.+?)__", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", safe)
    safe = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<i>\1</i>", safe)
    for key, replacement in placeholders.items():
        safe = safe.replace(key, replacement)
    return safe


def format_article_number(value: object) -> str:
    text = " ".join(str(value or "").split())
    if not text or text.lower() in {"document", "preamble"}:
        return ""
    match = re.search(r"មាត្រា\s*([០-៩0-9]+)", text, flags=re.IGNORECASE)
    text = match.group(1) if match else text
    text = text.rstrip(".-៖:;")
    return text.translate(str.maketrans("0123456789", "០១២៣៤៥៦៧៨៩"))

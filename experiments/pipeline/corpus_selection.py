"""Select OCR corpus files and load the five structured core laws."""
from __future__ import annotations

import csv
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from apps.core.shared.normalization import normalize_khmer

DOMAIN_PATTERNS = {
    "Traffic": re.compile(r"ចរាចរណ៍ផ្លូវគោក|ចរាចរផ្លូវគោក|ផ្លូវថ្នល់|ដឹកជញ្ជូន"),
    "Labour": re.compile(r"ច្បាប់ស្តីពីការងារ|ការងារ|ពលកម្ម|ពលករ|និយោជក|សហជីព|ប្រាក់ឈ្នួល"),
    "Human rights / social": re.compile(r"សិទ្ធិមនុស្ស|ស្ត្រី|កុមារ|ជនពិការ|សន្តិសុខសង្គម"),
}

CORE_PATTERNS = {
    "រដ្ឋធម្មនុញ្ញ": re.compile(r"រដ្ឋធម្មនុញ្ញ"),
    "ក្រមព្រហ្មទណ្ឌ": re.compile(r"ក្រម.*ព្រហ្មទណ្ឌ|ព្រហ្មទណ្ឌ"),
    "ក្រមនីតិវិធីព្រហ្មទណ្ឌ": re.compile(r"នីតិវិធី.*ព្រហ្មទណ្ឌ"),
    "ក្រមរដ្ឋប្បវេណី": re.compile(r"ក្រម.*រដ្ឋប្បវេណី|រដ្ឋប្បវេណី"),
    "ក្រមនីតិវិធីរដ្ឋប្បវេណី": re.compile(r"នីតិវិធី.*រដ្ឋប្បវេណី"),
}


def title_key(value: str) -> str:
    text = unicodedata.normalize("NFC", normalize_khmer(value)).lower()
    text = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    return text


def load_documents(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {
            str(row["document_id"]).strip(): row
            for row in csv.DictReader(stream)
            if row.get("document_id")
        }


def classify_title(title: str) -> str | None:
    value = normalize_khmer(title)
    for domain, pattern in DOMAIN_PATTERNS.items():
        if pattern.search(value):
            return domain
    return None


def is_core_title(title: str) -> bool:
    value = normalize_khmer(title)
    return any(pattern.search(value) for pattern in CORE_PATTERNS.values())


def select_and_reconcile_ocr(
    project_root: Path,
    documents_csv: Path,
    dry_run: bool = False,
) -> tuple[list[Path], dict[str, int]]:
    """Keep selected-domain OCR active; archive unrelated/core-duplicate OCR."""
    active = project_root / "data" / "text-ocr"
    archive = project_root / "data" / "archive" / "text-ocr"
    archive.mkdir(parents=True, exist_ok=True)
    documents = load_documents(documents_csv)

    def path_title(path: Path) -> str:
        return documents.get(path.stem, {}).get("title", "")

    counts = {"active_archived": 0, "archive_restored": 0, "selected": 0, "core_duplicates": 0}

    # First remove newly added active files that are outside the selected scope
    # or overlap a structured core-law title.
    for path in sorted(active.glob("*.txt")):
        title = path_title(path)
        selected = classify_title(title)
        destination = archive / path.name
        if selected is None or is_core_title(title):
            if is_core_title(title):
                counts["core_duplicates"] += 1
            if not dry_run:
                if destination.exists():
                    destination.unlink()
                shutil.move(str(path), str(destination))
            counts["active_archived"] += 1

    # Then restore archived files that belong to the selected domains and do
    # not overlap a structured core-law title.
    for path in sorted(archive.glob("*.txt")):
        title = path_title(path)
        if classify_title(title) is not None and not is_core_title(title):
            destination = active / path.name
            if not dry_run:
                if destination.exists():
                    destination.unlink()
                shutil.move(str(path), str(destination))
            counts["archive_restored"] += 1

    selected_paths = sorted(active.glob("*.txt"), key=lambda item: item.name)
    counts["selected"] = len(selected_paths)
    return selected_paths, counts


def load_core_articles(project_root: Path) -> list[dict[str, Any]]:
    source = project_root / "data" / "legal_codes" / "source" / "articles_chapter.json"
    books = json.loads(source.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    book_titles = {
        "Constitution": "រដ្ឋធម្មនុញ្ញ",
        "Criminal Code": "ក្រមព្រហ្មទណ្ឌ",
        "Criminal Procedure Code": "ក្រមនីតិវិធីព្រហ្មទណ្ឌ",
        "Civil Code": "ក្រមរដ្ឋប្បវេណី",
        "Civil Procedure Code": "ក្រមនីតិវិធីរដ្ឋប្បវេណី",
    }
    expected_books = set(book_titles)
    for book_name, articles in books.items():
        if book_name not in expected_books:
            continue
        for index, article in enumerate(articles, start=1):
            name = normalize_khmer(article.get("name", ""))
            if book_name == "Criminal Code" and "ស្ទួន" in name:
                continue
            text = normalize_khmer(article.get("description", ""))
            if not text:
                continue
            article_number = article.get("id", index)
            title = normalize_khmer(article.get("book", book_titles[book_name]))
            records.append({
                "article_id": f"core-{book_name}-{article_number}",
                "document_id": f"core-{book_name}",
                "article_number": article_number,
                "chapter_number": article.get("chapter", ""),
                "chapter_title": normalize_khmer(article.get("chapter", "")),
                "section_number": None,
                "section_title": "",
                "title": title,
                "document_type": "Core law",
                "domain": "Core law",
                "publication_date": "",
                # The public site is the viewable source page. Keep the PDF
                # field separate as a fallback, but do not use it as the
                # primary citation link.
                "source_url": "https://www.khmerlawcode.com/",
                "pdf_url": "",
                "text_file": str(source),
                "preamble": "",
                "text": text,
                "search_text": normalize_khmer(f"{title}\nមាត្រា {article_number}\n{text}"),
                "normalization_version": "legal-cleaning-v1-khmer-normalization-v2",
            })
    if len(records) != 3337:
        raise ValueError(f"Expected 3337 core-law articles, found {len(records)}")
    return records

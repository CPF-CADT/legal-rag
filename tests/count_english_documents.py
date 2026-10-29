"""Count likely English/Latin documents from the scraper CSV.

This script is read-only with respect to PDFs. It only creates a CSV report
of the records that should be reviewed before moving any files.
"""

import csv
import re
from pathlib import Path


# Change these paths directly if your CSV is stored elsewhere.
INPUT_CSV = Path("documents.csv")
REPORT_CSV = Path("english_documents_report.csv")

KHMER_RE = re.compile(r"[\u1780-\u17FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def classify_text(text: str) -> str:
    """Classify text using Unicode characters in the document title."""
    has_khmer = bool(KHMER_RE.search(text))
    has_latin = bool(LATIN_RE.search(text))

    if has_latin and not has_khmer:
        return "english_or_latin"
    if has_khmer and has_latin:
        return "mixed_khmer_english"
    if has_khmer:
        return "khmer"
    return "unknown"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"CSV file not found: {INPUT_CSV.resolve()}")

    records = []
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "title" not in reader.fieldnames:
            raise ValueError("The CSV must contain a 'title' column.")

        for row in reader:
            row["detected_language"] = classify_text(row.get("title", ""))
            records.append(row)

    english = [
        row for row in records
        if row["detected_language"] == "english_or_latin"
    ]
    mixed = [
        row for row in records
        if row["detected_language"] == "mixed_khmer_english"
    ]
    khmer = [row for row in records if row["detected_language"] == "khmer"]
    unknown = [row for row in records if row["detected_language"] == "unknown"]
    downloaded_english = [
        row for row in english if row.get("status", "").lower() == "downloaded"
    ]

    report_fields = [
        "document_id",
        "title",
        "status",
        "local_pdf_path",
        "pdf_url",
        "detected_language",
    ]
    with REPORT_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=report_fields)
        writer.writeheader()
        for row in english:
            writer.writerow({field: row.get(field, "") for field in report_fields})

    print(f"Total records:              {len(records)}")
    print(f"English/Latin candidates:   {len(english)}")
    print(f"Downloaded English PDFs:    {len(downloaded_english)}")
    print(f"Mixed Khmer + English:      {len(mixed)}")
    print(f"Khmer-only titles:          {len(khmer)}")
    print(f"Unknown titles:             {len(unknown)}")
    print(f"Report written to:          {REPORT_CSV.resolve()}")

    if english:
        print("\nEnglish/Latin candidates:")
        for row in english:
            print(
                f"- {row.get('document_id', '')}: "
                f"{row.get('title', '')} "
                f"[{row.get('status', '')}]"
            )


if __name__ == "__main__":
    main()

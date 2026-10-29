"""Move English/Latin PDF candidates into a separate folder.

The classification matches count_english_documents.py: titles containing
Latin letters and no Khmer characters are treated as English/Latin.
"""

import csv
import re
import shutil
from pathlib import Path


# Change these paths directly if needed.
INPUT_CSV = Path("documents.csv")
SOURCE_DIR = Path("data/pdfs")
DEST_DIR = Path("data/pdfs-en")

# Set to True to preview actions without moving files.
DRY_RUN = False

KHMER_RE = re.compile(r"[\u1780-\u17FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def is_english_title(title: str) -> bool:
    return bool(LATIN_RE.search(title)) and not bool(KHMER_RE.search(title))


def source_path(row: dict[str, str]) -> Path:
    """Use the CSV path when valid; otherwise use SOURCE_DIR/document_id.pdf."""
    csv_path = Path(row.get("local_pdf_path", ""))
    if csv_path.exists():
        return csv_path
    return SOURCE_DIR / f"{row['document_id']}.pdf"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"CSV file not found: {INPUT_CSV.resolve()}")

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped_missing = 0
    skipped_existing = 0
    candidates = 0

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not {"document_id", "title"}.issubset(reader.fieldnames):
            raise ValueError("The CSV must contain 'document_id' and 'title' columns.")

        for row in reader:
            if not is_english_title(row.get("title", "")):
                continue

            candidates += 1
            source = source_path(row)
            destination = DEST_DIR / source.name

            if not source.is_file():
                skipped_missing += 1
                print(f"MISSING: {source}")
                continue

            if destination.exists():
                skipped_existing += 1
                print(f"SKIP already moved: {destination}")
                continue

            print(f"MOVE: {source} -> {destination}")
            if not DRY_RUN:
                shutil.move(str(source), str(destination))
            moved += 1

    mode = "DRY RUN" if DRY_RUN else "MOVE COMPLETE"
    print(f"\n{mode}")
    print(f"English/Latin candidates: {candidates}")
    print(f"Moved:                   {moved}")
    print(f"Missing source PDFs:      {skipped_missing}")
    print(f"Already in destination:   {skipped_existing}")
    print(f"Destination:              {DEST_DIR.resolve()}")


if __name__ == "__main__":
    main()

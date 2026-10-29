# NCDD LegalRAG Project Guide

This project downloads legal documents from the NCDD website and processes them with Gemini OCR.

## Main folders

### `infra/`

Terraform infrastructure for AWS:

- EC2 instance
- EBS data volume
- Security group
- Server setup script
- Terraform variables and outputs

Terraform state files contain infrastructure information and should not be committed publicly.

### `web-scraper/`

Downloads documents from the NCDD website.

- `main.py` — direct scraper configuration and pipeline entry point.
- `scraper.py` — discovers document records, reads metadata, and coordinates downloads.
- `downloader.py` — downloads and validates PDF files.

The scraper saves PDFs and its CSV checkpoint under `data/` when run from the project.

### `ocr-process/`

Extracts text from downloaded PDFs using Gemini.

- `main.py` — OCR configuration and entry point.
- `processor.py` — splits PDFs into batches, sends requests, saves text, and resumes work.
- `gemini_client.py` — Gemini API client.
- `key_manager.py` — rotates rate-limited keys and disables invalid keys.

Put `keys.txt` in the project root, beside `ocr-process/`:

```text
legal-rag/
├── keys.txt
├── ocr-process/
└── web-scraper/
```

Use one Gemini API key per line. Never commit this file.

### `data/`

Runtime data stored on the EBS volume in production:

- `pdfs/` — downloaded source PDFs.
- `ocr/chunks/` — ten-page PDF batches.
- `ocr/chunk_text/` — extracted text for each batch.
- `ocr/text/` — final document text files.
- `ocr/usage/` — Gemini usage records.
- `checkpoints/` — CSV files used for resume and recovery.
- `logs/` — scraper and OCR logs.

### `tests/`

Tests for checkpoint handling, retry behavior, and crash recovery.

### `ipynb/`

Older exploratory notebooks for downloading and testing OCR approaches.

### `temp/`

Temporary helper scripts, such as English-document counting and PDF moving tools.

## Pipeline flow

```text
NCDD website
    ↓
web-scraper
    ↓
data/pdfs/
    ↓
ocr-process splits PDFs into ten-page batches
    ↓
Gemini OCR with key rotation
    ↓
data/ocr/text/
```

## Running the scraper

From the project root:

```bash
python3 web-scraper/main.py
```

The scraper records document status in:

```text
data/checkpoints/documents.csv
```

It skips valid PDFs that already exist and retries failed downloads.

## Running OCR

From the project root:

```bash
python3 ocr-process/main.py
```

OCR resumes from its CSV checkpoints and does not create final text for incomplete documents.

## EC2 storage

In production, `data/` should point to the mounted EBS volume. This keeps PDFs, OCR output, checkpoints, and logs available after restarting the EC2 instance.

## Important safety rules

- Do not run two scraper or OCR processes at the same time.
- Check the logs before restarting a failed process.
- Do not delete checkpoint CSV files unless you intentionally want to restart processing.

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

### `react-client/`

The React frontend.

### `bot/`

The Telegram bot application. This folder is reserved for bot code.

### `data-pipeline/`

All collection, OCR, transformation, cleaning, runtime data, tests, and exploratory notebooks live here.

- `collection/` — collection notebooks and references.
- `ocr-process/` — OCR notebooks and references.
- `automation-process/download/` — runnable NCDD scraper and downloader.
- `automation-process/ocr/` — runnable OCR processor, Gemini client, and key manager.
- `transformation/` — lexicon and derived-data transformations.
- `cleaning/` — document classification and file organization utilities.
- `data/` — PDFs, OCR output, checkpoints, logs, and temporary pipeline data.
- `testable/` — notebooks and Python tests. Notebooks are kept directly in this folder.

The collection code saves PDFs and checkpoints under `data-pipeline/data/`.

### `data-pipeline/automation-process/download/`

Downloads documents from the NCDD website.

- `main.py` — direct scraper configuration and pipeline entry point.
- `scraper.py` — discovers document records, reads metadata, and coordinates downloads.
- `downloader.py` — downloads and validates PDF files.

### `data-pipeline/automation-process/ocr/`

Extracts text from downloaded PDFs using Gemini.

- `main.py` — OCR configuration and entry point.
- `processor.py` — splits PDFs into batches, sends requests, saves text, and resumes work.
- `gemini_client.py` — Gemini API client.
- `key_manager.py` — rotates rate-limited keys and disables invalid keys.

Put `keys.txt` in the project root, beside `data-pipeline/`:

```text
legal-rag/
├── keys.txt
├── data-pipeline/
├── react-client/
└── bot/
```

Use one Gemini API key per line. Never commit this file.

### `data-pipeline/data/`

Runtime data stored on the EBS volume in production:

- `pdfs/` — downloaded source PDFs.
- `ocr/chunks/` — ten-page PDF batches.
- `ocr/chunk_text/` — extracted text for each batch.
- `ocr/text/` — final document text files.
- `ocr/usage/` — Gemini usage records.
- `checkpoints/` — CSV files used for resume and recovery.
- `logs/` — scraper and OCR logs.

### `data-pipeline/testable/`

General experiments and Python tests. Stage-specific notebooks are kept beside their stage:
collection notebooks in `collection/`, OCR notebooks in `ocr-process/`, and article transformation in `transformation/`.

## Pipeline flow

```text
NCDD website
    ↓
data-pipeline/automation-process/download
    ↓
data-pipeline/data/pdfs/
    ↓
data-pipeline/automation-process/ocr splits PDFs into ten-page batches
    ↓
Gemini OCR with key rotation
    ↓
data-pipeline/data/ocr/text/
```

## Running the scraper

From the project root:

```bash
python3 data-pipeline/automation-process/download/main.py
```

The scraper records document status in:

```text
data-pipeline/data/checkpoints/documents.csv
```

It skips valid PDFs that already exist and retries failed downloads.

## Running OCR

From the project root:

```bash
python3 data-pipeline/automation-process/ocr/main.py
```

OCR resumes from its CSV checkpoints and does not create final text for incomplete documents.

## EC2 storage

In production, `data-pipeline/data/` should point to the mounted EBS volume. This keeps PDFs, OCR output, checkpoints, and logs available after restarting the EC2 instance.

## Important safety rules

- Do not run two scraper or OCR processes at the same time.
- Check the logs before restarting a failed process.
- Do not delete checkpoint CSV files unless you intentionally want to restart processing.

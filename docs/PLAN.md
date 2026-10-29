# Final Plan: NCDD LegalRAG Pipeline

Infrastructure will be implemented last. First, build and test the complete Python pipeline locally using the existing notebooks as references.

## Target structure

```text
legal-rag/
├── web-scraper/
│   ├── main.py
│   ├── scraper.py
│   └── downloader.py
│
├── ocr-process/
│   ├── main.py
│   ├── processor.py
│   ├── gemini_client.py
│   └── key_manager.py
│
├── data/
│   ├── pdfs/
│   ├── ocr/
│   │   ├── chunks/
│   │   ├── chunk_text/
│   │   ├── text/
│   │   └── usage/
│   ├── checkpoints/
│   │   ├── documents.csv
│   │   ├── ocr_batches.csv
│   │   └── api_keys.csv
│   └── logs/
│
├── keys.txt
└── PROMT.md
```

The application will use pure Python scripts, direct configuration inside the scripts, CSV checkpoints, and sequential processing.

## Phase 1: Prepare the Python project

Create the application folders and direct configuration sections in:

```text
web-scraper/main.py
ocr-process/main.py
```

Configuration will include:

- NCDD URL and category.
- Retry count.
- Request delay.
- PDF and OCR paths.
- OCR batch size: 10 pages.
- Gemini model.
- Cooldown time.
- Log and checkpoint paths.

No database, CLI framework, `.env`, YAML, JSON configuration, Docker, or Redis will be used.

## Phase 2: Build the web scraper

Convert the logic from `ncdd_law_downloader.ipynb`.

Reuse:

- Playwright discovery.
- Pagination handling.
- Metadata extraction.
- PDF URL detection.
- PDF validation.
- Retry and delay logic.
- Temporary `.part` downloads.

The scraper will:

1. Discover NCDD records.
2. Save records to `documents.csv`.
3. Skip valid PDFs already downloaded.
4. Download missing PDFs.
5. Validate each PDF.
6. Update the CSV after every document.
7. Continue safely after individual failures.

### `documents.csv`

```text
document_id
title
detail_url
pdf_url
local_pdf_path
status
retry_count
error
updated_at
```

Statuses:

```text
discovered
downloaded
no_pdf
failed
```

## Phase 3: Build the OCR processor

Convert the logic from `ncdd_law_ocr_gemini_api.ipynb`.

Changes from the notebook:

- Change chunk size from 9 pages to 10 pages.
- Change paths to the new `data/` directories.
- Replace the single API key with `keys.txt`.
- Replace text-file-only checkpointing with `ocr_batches.csv`.
- Save each batch result before continuing.
- Create final document text only when all batches succeed.
- Fix the usage log field separator bug.

The OCR script will:

1. Read downloaded PDFs from `documents.csv`.
2. Split PDFs into 10-page chunks.
3. Skip completed OCR batches.
4. Send incomplete batches to Gemini.
5. Save Khmer text.
6. Save usage information.
7. Update `ocr_batches.csv`.
8. Combine completed batches into one final text file.

### `ocr_batches.csv`

```text
document_id
batch_number
page_start
page_end
chunk_path
text_path
status
retry_count
api_key_id
error
updated_at
```

Statuses:

```text
pending
processing
completed
failed
```

## Phase 4: Add API key rotation

Implement `key_manager.py`.

It will:

- Read keys from `keys.txt`.
- Select the next available key.
- Move rate-limited keys to the back of the queue.
- Temporarily pause limited keys.
- Disable invalid keys.
- Save key state to `api_keys.csv`.
- Stop safely when no usable key remains.

### `api_keys.csv`

```text
key_id
status
limited_until
failure_count
last_error
updated_at
```

Actual API keys will not be written to logs or CSV files.

## Phase 5: Add recovery and safe CSV updates

The scripts must resume after interruption.

For downloads:

- Skip valid existing PDFs.
- Ignore incomplete `.part` files.
- Retry failed records.

For OCR:

- Skip completed batches.
- Retry incomplete or failed batches.
- Do not create incomplete final text files.

CSV updates should be written to a temporary file first, then replace the original CSV to reduce corruption risk.

## Phase 6: Local testing

Test locally before creating EC2 infrastructure:

1. Download a small number of documents.
2. Process one small PDF.
3. Stop the scraper during a download.
4. Restart and verify resume behavior.
5. Stop OCR during a Gemini request.
6. Restart and verify completed batches are skipped.
7. Test rate-limited key rotation.
8. Test invalid-key disabling.
9. Run each script twice and verify no duplicate processing.
10. Verify all output paths and CSV statuses.

## Phase 7: Infrastructure implementation

Only after the Python pipeline works locally, create:

```text
infra/
├── main.tf
├── variables.tf
├── outputs.tf
└── setup.sh
```

Terraform will provision:

- EC2 instance.
- 40 GB EBS volume.
- Security group.
- IAM configuration if needed.
- Persistent EBS mount.

`setup.sh` will install:

- Python.
- Required Python packages.
- Playwright.
- Chromium.
- Application directories.

## Phase 8: EC2 deployment

1. Copy the tested Python scripts to EC2.
2. Mount EBS as the data directory.
3. Copy `keys.txt` securely.
4. Run the scraper script.
5. Review `documents.csv`.
6. Run the OCR script separately.
7. Review `ocr_batches.csv`.
8. Confirm final Khmer text files.
9. Process the complete NCDD collection.

Final order:

```text
Python project
→ Web scraper
→ CSV checkpoints
→ OCR processor
→ API key rotation
→ Recovery testing
→ Terraform and EC2
→ Full production run
```

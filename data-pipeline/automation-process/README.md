# Automation process

Runnable Python processes for collecting data and running OCR.

This folder automates the repeatable steps after collection notebooks. It downloads or resumes PDF collection, records download errors and retries, then runs OCR on the available PDFs and saves document text for transformation.

## Flow

```text
NCDD records
    → download PDFs
    → update checkpoints
    → run OCR
    → save text for article transformation
```

## Download data

```bash
python3 data-pipeline/automation-process/download/main.py
```

## Run OCR

```bash
python3 data-pipeline/automation-process/ocr/main.py
```

Run both from the project root. The download process saves PDFs and checkpoints
under `data-pipeline/data/`; the OCR process reads those PDFs and saves OCR
results in the same data directory.

The scripts do not build the final article JSON. That work is handled by the transformation notebook.

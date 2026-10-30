# Automation process

Runnable Python processes for collecting data and running OCR.

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

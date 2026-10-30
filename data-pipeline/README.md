# Data pipeline

This folder contains the data workflow:

- `collection/` — collection notebooks and references.
- `ocr-process/` — OCR notebooks and references.
- `automation-process/download/` — runnable download code.
- `automation-process/ocr/` — runnable OCR code.
- `transformation/` — transform OCR text into structured CSV and other datasets.
- `cleaning/` — clean, classify, and organize collected documents.
- `testable/` — general tokenizer/lexicon experiments and Python tests.
- `data/` — local inputs, outputs, checkpoints, logs, and temporary data.

Run scripts from the project root:

```bash
python3 data-pipeline/automation-process/download/main.py
python3 data-pipeline/automation-process/ocr/main.py
```

Notebooks are kept beside the stage they explore: collection notebooks are in
`collection/`, OCR notebooks are in `ocr-process/`, article transformation is in
`transformation/`, and general experiments are in `testable/`.

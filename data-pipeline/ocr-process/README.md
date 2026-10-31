# OCR Processing

This stage converts downloaded legal PDFs into Khmer text for the transformation stage.

## Flow

```text
Downloaded PDFs
    → OCR with KhmerOCR, Netra-OCR, or Gemini Vision
    → save document text
    → pass text to article transformation
```

## Notebooks

- `ncdd_law_ocr_khmerocr.ipynb` — Khmer OCR processing
- `ncdd_law_ocr_netra.ipynb` — Netra-OCR processing
- `ncdd_law_ocr_gemini_api.ipynb` — Gemini Vision transcription

OCR outputs are stored under `data/` and are later transformed into structured article JSON. Original PDFs remain the source for verification.

# Document Collection

This stage performs responsible web crawling and scraping of the NCDD Digital Library. It discovers legal documents, extracts metadata and PDF links, downloads and validates the original PDFs, and records collection results.

## Flow

```text
NCDD Digital Library
    → discover document pages
    → extract metadata and PDF links
    → download and validate PDFs
    → archive source files and collection records
    → pass documents to OCR processing
```

The goal is to create a complete, traceable, and reusable source collection for the legal-data pipeline.

## Outputs

```text
data/temp/ncdd_laws/
├── pdfs/            # Downloaded PDFs
├── metadata.csv     # Document metadata
├── audit.csv        # Collection results
└── unresolved.csv   # Failed records
```

The collected documents are passed to the OCR and transformation stages.

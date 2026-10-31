# Legal OCR Text Cleaning and Article Structuring

This folder contains the transformation notebook:

- `legal_article_preprocessing.ipynb`

The notebook converts cleaned Khmer legal OCR/transcript text into article-level JSON files for search indexing and embeddings.

## Process

```text
OCR/transcript text
    → remove formatting noise
    → remove page numbers and repeated appendix content
    → detect chapters, sections, and articles
    → create structured JSON
    → record processing status
```

## Cleaning decisions

The process:

- Preserves Khmer legal wording, numbers, names, dates, and legal references.
- Extracts document metadata, chapters, sections, and articles.
- Supports article markers such as `[START_ARTICLE:1]`.
- Supports OCR variations such as `មាត្រា ១` and `មាត្រាមួយ`.
- Removes standalone page numbers such as `១៦០១`, `២៥៤`, and `1/3`.
- Removes zero-width characters, repeated spaces, decorative symbols, and search-irrelevant punctuation.
- Removes article heading prefixes from article text because the article number is stored separately.
- Removes signing blocks, signature names, repeated page headers, and unrelated appendix tables from article content.
- Keeps the final legal article itself; only non-article closing material after it is removed.
- Preserves meaningful list signs such as `-` and `+`.

## Data skipped from article JSON

Documents without reliable article structure are skipped from the final article JSON dataset. Examples include research documents, policy documents, poetry collections, legal Q&A documents, and regulations without clear article boundaries.

Non-law documents are also not forced into the legal-article schema. They are skipped from the article JSON output because their structure is different from laws and regulations. These files are not deleted and remain available for a future document-level search pipeline.

Skipped documents are not deleted. Their source files remain available and their status is recorded in:

```text
data/checkpoints/documents_pipeline.csv
```

## Outputs

Article JSON files are written to:

```text
data/processed/json/
```

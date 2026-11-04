# Current Semantic Search Pipeline

This report documents the current production flow from notebook 03 through notebook 09. The system uses BGE-M3 semantic retrieval. It does not use BM25, hybrid search, a cross-encoder reranker, fine-tuning, translation, or summarization.

## Pipeline overview

```text
OCR text
  ↓
03  Parse and clean legal documents
  ↓
04  Flatten nested documents into article records
  ↓
05  Normalize Khmer search text
  ↓
06  Split articles into ≤450-token chunks and create embeddings
  ↓
07  Store BGE-M3 chunk vectors in ChromaDB
  ↓
08  Semantic search chunks, group by article, display full articles
  ↓
09  Evaluate article-level and chunk-level ranking
```

## 03 — Legal OCR preprocessing

This notebook converts each OCR text file into a structured legal document.

It performs the following operations:

- Unicode NFKC normalization.
- Removal of zero-width characters and non-breaking spaces.
- Removal of decorative dots and search-noise punctuation such as `៖`, `។`, `៕`, `:`, `;`, `!`, and `?`.
- Collapsing repeated spaces.
- Removal of likely page-number-only lines when page context supports that decision.
- Detection of document number, chapters, sections, and article headings.
- Removal of the article heading from the article body.
- Removal of closing/signature information from article text when detected.
- Preservation of the preamble instead of discarding text before the first article.
- Preservation of meaningful line breaks, while preventing repeated blank lines.

It does not translate, summarize, tokenize, embed, or silently correct legal wording.

The output remains hierarchical: document → chapter → section → article.

## 04 — Prepare article records

This notebook flattens the nested legal structure into one JSONL record per article.

Each article receives a canonical ID:

```text
{document_id}-{article_number}
```

Each record keeps:

- Full article text.
- Document title and document number.
- Document ID and article number.
- Chapter and section metadata.
- Source and PDF URLs.

If the same article ID occurs more than once, the physical record ID receives a suffix such as `-2`, but the canonical `article_id` remains available for grouping and evaluation.

Current run: 546 article records were prepared.

## 05 — Normalize article search text

This is conservative search normalization. It creates `search_text` while preserving the original `text` field.

It performs:

- Unicode NFC normalization.
- Removal of the zero-width characters `\u200b`, `\u200c`, and `\u200d`.
- Replacement of the non-breaking space `\u00a0` with a normal space.
- Collapsing repeated spaces and tabs.
- Trimming each line.
- Removing empty lines.
- Reducing repeated newlines to one newline.

It does not remove Khmer letters, Khmer vowels, Khmer signs, or Khmer digits. The punctuation cleanup in notebook 03 is separate from this normalization step; notebook 03 removes selected punctuation such as `៖`, `។`, `៕`, `:`, `;`, `!`, and `?` from search text while preserving the legal content.

It does not:

- Remove Khmer stop words.
- Stem or lemmatize words.
- Translate Khmer.
- Segment Khmer words.
- Change legal wording.
- Create embeddings.

Current run: 546 normalized article records.

## 06 — Create chunks and embeddings

The chunker works inside each article. It does not combine text from different articles.

Chunking rules:

- Maximum budget: 450 tokens.
- Context tokens are reserved for document title, article number, chapter, and section.
- Recursive split order:
  1. Paragraph boundaries.
  2. Newline boundaries.
  3. Khmer and general sentence punctuation.
  4. Zero-width boundaries.
  5. Whitespace.
  6. Character boundaries as a final fallback.
- Chunks shorter than 80 characters are merged with the previous chunk when possible.
- Article context is prefixed to the embedding text.

The notebook generates embeddings for three models, but the current production search uses:

```text
BAAI/bge-m3
```

Embeddings are normalized before storage, enabling cosine-similarity ranking through dot-product equivalence.

## 07 — Store vectors in ChromaDB

Production collection:

```text
legal_chunks_bge_m3_450
```

The collection stores:

- Chunk IDs.
- Chunk text.
- Parent article ID.
- Document and article metadata.
- Normalized embedding vectors.

Current collection size: 1,193 chunks.

## 08 — Semantic search and ranking

Search process:

1. Normalize the query with Unicode NFC and whitespace cleanup.
2. Encode the query using BGE-M3.
3. Retrieve up to 100 candidate chunks, with a minimum of `top_k × 20`.
4. Read cosine distances from ChromaDB.
5. Group matching chunks by canonical `article_id`.
6. Rank each article by the distance of its best matching chunk.
7. Return the top five articles.
8. Display the complete article text, not only the matching chunk.
9. Include the best two matching chunks as evidence.

This is semantic retrieval with article-level aggregation. It is not a separate reranker. The ranking formula is effectively:

```text
article_score(article) = best semantic similarity among its retrieved chunks
```

The search index is chunk-based, but the user-facing result is full-article-based.

Current index: 468 canonical article IDs and 1,193 chunks.

## 09 — Evaluation

The evaluation notebook compares two ranking approaches using the same BGE-M3 query vectors:

### Article-level ranking

It compares the query vector directly with article-level embeddings and ranks complete articles.

### Chunk-level ranking

It compares the query vector with chunk embeddings, keeps the highest-scoring chunk per article, and ranks articles by that score.

Evaluation metrics:

- Hit@3.
- Hit@5.
- Recall@5.
- MRR@3.
- nDCG@3.

The relevance mapping is stored in:

- `data-pipeline/evaluation/data/relevance_mapping.json`

The current evaluation contains 20 queries, but only 5 are eligible because the expected articles for the other 15 queries are not in the current 11-document corpus.

Current eligible-query results:

| Ranking level | Hit@3 | Hit@5 | MRR@3 | nDCG@3 |
|---|---:|---:|---:|---:|
| Article-level | 0.80 | 1.00 | 0.80 | 0.80 |
| Chunk-level | 0.80 | 1.00 | 0.70 | 0.7262 |

## Important interpretation

The current system is optimized for finding relevant legal articles semantically. Chunks are an internal retrieval unit. The final result should remain the complete legal article so that users do not lose legal context.

The current evaluation is not yet a full-corpus benchmark because 15 of 20 expected articles are absent from the indexed corpus. The next reliable measurement should use queries whose expected articles are all present, or expand the OCR corpus before comparing models.

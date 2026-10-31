# Index Construction

This stage prepares article-level records for BM25 and semantic search.

Main notebooks:

- `prepare_articles.ipynb`
- `normalize_articles.ipynb`

Embedding generation is isolated in the `embedding/` folder and uses notebooks:

- `embedding/embedding_pipeline.ipynb`
- `embedding/generate_article_embeddings.ipynb`
- `embedding/generate_chunk_embeddings.ipynb`

## Phase 1: Prepare articles

The script reads the canonical nested JSON files and creates a derived JSONL file. It does not tokenize, segment, embed, or replace the original JSON.

The notebook can be run cell by cell. The equivalent command-line script is:

```bash
python3 data-pipeline/index-construction/prepare_articles.py
```

Phase 2 normalization uses `articles.jsonl` and writes:

```text
data/processed/search/articles_normalized.jsonl
```

Phase 3 generates separate vector datasets for model comparison. All four models use the same input records, metadata alignment, normalization, and output format. The shared configuration and output contract are documented in `embedding_pipeline.ipynb`.

Run `generate_article_embeddings.ipynb` from the project root. Run `generate_chunk_embeddings.ipynb` when chunk-level retrieval is needed.

Each experiment writes its own vectors, metadata, and manifest under `data/processed/embeddings/`:

```text
articles_labse.npy
articles_labse_metadata.jsonl
articles_labse_manifest.json

articles_granite_311m_r2.npy
articles_granite_311m_r2_metadata.jsonl
articles_granite_311m_r2_manifest.json

articles_sealion_e5_600m.npy
articles_sealion_e5_600m_metadata.jsonl
articles_sealion_e5_600m_manifest.json

articles_albert_khmer_small.npy
articles_albert_khmer_small_metadata.jsonl
articles_albert_khmer_small_manifest.json
```

The `.npy` row order matches the corresponding metadata JSONL row order. The manifest records the model name and vector dimension so the datasets can be evaluated fairly. The pipeline uses the normalized `search_text` field and does not perform Khmer tokenization or word segmentation.

## Model distinction

`ibm-granite/granite-embedding-311m-multilingual-r2` is the selected Granite model. It is a retrieval-trained multilingual embedding model with enhanced support for Khmer. It produces 768-dimensional vectors and is loaded directly from Hugging Face through SentenceTransformers.

`seanghay/albert-khmer-small` is a Khmer masked-language model, not a retrieval-trained embedding model. Its output is included as a lightweight Khmer-specific baseline using mean pooling. It must be evaluated against the retrieval-trained models before being considered for semantic search.

## Khmer normalization

Normalization makes document text and user queries use a consistent form:

- **Unicode character order** — `ស្តី` is represented as `ស + ្ + ត + ី` and normalized to one canonical internal order. A form such as `ស + ី + ត + ្ + ត` contains an extra `ត` and is not the same word.
- **Invisible characters** — `ច្បាប់​ស្តីពី` becomes `ច្បាប់ស្តីពី` when a hidden zero-width character is present.
- **Whitespace** — `ច្បាប់  ស្តីពី` becomes `ច្បាប់ ស្តីពី`.
- **Non-breaking spaces** — `មាត្រា ១` becomes `មាត្រា ១`.
- **Punctuation** — `ច្បាប់នេះ៖` follows the same cleaned punctuation rules as other article text.

This step does not correct spelling, translate text, tokenize words, or change legal meaning.

Output:

```text
data/processed/search/articles.jsonl
```

Each record keeps the article text, document and article identifiers, chapter/section context, and official source URLs.

The base reference is `document_id-article_number`. If OCR contains the same article number more than once, the database ID receives an occurrence suffix such as `1004-71-2`.

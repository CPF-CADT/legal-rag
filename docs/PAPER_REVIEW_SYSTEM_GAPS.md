# Research Paper Review: Current Semantic Search Gaps

## Papers reviewed

- A Comparative Study of Language Models for Khmer Retrieval-Augmented Question Answering.
- Evaluation of Chunking Strategies for Effective Text Embedding in Low-Resource Language on Agricultural Documents.
- Khmer Semantic Search Engine: Digital Information Access and Document Retrieval.
- Khmer Word Search: Challenges, Solutions, and Semantic-Aware Search.

## What the current system already does well

- Uses BGE-M3, which is also evaluated as a strong Khmer dense retriever in the comparative study.
- Uses offline document processing, chunking, embedding, vector indexing, and top-k retrieval.
- Preserves article metadata and displays the complete legal article after chunk retrieval.
- Uses recursive structure-aware chunking instead of relying only on Khmer sentence boundaries.
- Evaluates retrieval with Hit@k, MRR, and nDCG.

## Main weaknesses

### 1. The evaluation corpus is too small and incomplete

The current evaluation has 20 queries, but only 5 expected articles exist in the current indexed corpus. The current score is therefore not a full 20-query benchmark.

The comparative paper uses 200 expert-created Khmer question-answer pairs. The chunking paper uses 5-fold cross-validation over 18 question-answer pairs. Both provide stronger evidence than the current five eligible queries.

### 2. The current chunk size is not justified for this legal corpus

The current system uses a maximum of 450 BGE-M3 tokens. The chunking paper found that structure-preserving recursive splitting at 300 characters performed best in its Khmer agricultural evaluation, outperforming sentence-based, Khmer-aware, and LLM-based alternatives.

The units are different: 300 characters is not the same as 450 tokens. The current system must run a legal-domain ablation instead of assuming 450 tokens is optimal.

### 3. Khmer punctuation is removed before chunking

Notebook 03 removes Khmer punctuation such as `។`, `៕`, and `៖`. However, the chunking paper recommends preserving Khmer sentence markers and structural cues during segmentation. Removing them can make sentence and list boundaries less clear.

The canonical legal text and the chunking text should not lose punctuation. If punctuation-free text is useful for retrieval, it should be a separate field rather than replacing the source used for chunking.

### 4. Khmer normalization is incomplete

The current normalization handles Unicode NFC, zero-width characters, non-breaking spaces, and whitespace. It does not handle the Khmer search problems described in the word-search paper:

- Different character orders that render identically.
- Stacked versus unstacked spelling variants.
- Missing vowels or diacritics.
- Grapheme-level spelling errors.
- Phonetic spelling errors.
- Semantically related words unknown to the query author.

This means a query with a spelling or character-order variation may still miss the correct article.

### 5. Ranking uses only one best chunk per article

The current search ranks an article by the best matching chunk. One short, accidentally similar chunk can therefore outrank an article whose several chunks are collectively more relevant.

The papers use top-k chunk retrieval and file-level evaluation. The legal system should compare best-chunk, mean top-2, mean top-3, and weighted multi-chunk aggregation.

### 6. Article-level evaluation is not fully produced by the main flow

Notebook 09 loads `articles_bge_m3_450.npy`, but notebook 06 mainly creates chunk embeddings. Article embeddings are produced by a separate experimental notebook. This makes the article-level result less reproducible from the production notebook sequence.

Article embedding generation should be part of the main production flow or article-level evaluation should be removed until it is generated from the same input snapshot.

### 7. The current system has no Khmer lexical recovery layer

The KSE papers describe keyword extraction, dictionary matching, ontology relations, and ranking signals. The newer KSE research also evaluates character n-gram BM25 because Khmer word boundaries and spelling variation make word-based matching unreliable.

The current system is dense-only. It can miss exact legal terms, article numbers, names, and spelling variants even when the answer is lexically present.

This is intentionally outside the current pure-semantic phase, but it remains the main research-backed next retrieval improvement.

### 8. Model comparison is not yet legal-domain controlled

The current project previously compared SEA-LION, Granite, and BGE-M3, but the current production flow uses only BGE-M3. The comparative paper also tested BGE-M3, Jina-Embeddings-v3, and Qwen embeddings on the same Khmer evaluation set.

Model conclusions should be based on the same legal queries, same chunk versions, same candidate count, and same metrics.

## Recommended solution order

### Priority 1 — Make the benchmark valid

- Expand the legal corpus so all evaluation queries have their expected articles.
- Build at least 50–100 legal queries before making model claims; 200 is a stronger target based on the comparative paper.
- Use three-level relevance: `2 = direct`, `1 = partial`, `0 = irrelevant`.
- Add 5-fold or repeated-query evaluation where the query count allows it.
- Report article-level Hit@3/5, Recall@5/10, MRR@3/10, nDCG@3/10, and file/document Hit@k.

### Priority 2 — Run a legal chunking ablation

Create identical BGE-M3 indexes for:

- Recursive 300-character chunks.
- Recursive 450-token chunks.
- Recursive 600-token chunks.
- Article-preserving chunks with section context.

Compare them on the same legal qrels. Keep the best chunking strategy based on MRR, nDCG, and article Hit@k—not on chunk count alone.

### Priority 3 — Preserve source text and improve normalization

- Keep canonical article text unchanged except for safe Unicode cleanup.
- Preserve `។`, `៕`, `៖`, and list markers in the chunking source.
- Create a separate `retrieval_text` field if punctuation-stripped text is needed.
- Add explicit Khmer character-order normalization based on Khmer canonical character clusters.
- Add a grapheme spell-variant table first; measure it before adding phoneme-based correction.
- Keep the original query and record every generated normalized variant for debugging.

### Priority 4 — Test multi-chunk article aggregation

Compare these article scores:

```text
best_chunk_score
mean(top_2_chunk_scores)
mean(top_3_chunk_scores)
0.7 * best + 0.3 * second_best
```

Use the same candidate pool for every method. This directly tests whether the current best-chunk rule is causing the article-level ranking weakness.

### Priority 5 — Make article embeddings reproducible

- Generate article embeddings in the production embedding notebook.
- Save the exact input hash, article ID order, model name, and embedding dimension in the manifest.
- Ensure notebook 09 loads vectors generated from the same corpus snapshot as the chunk vectors.

### Priority 6 — Add lexical retrieval after dense-only evaluation

After the pure semantic baseline is stable, implement a character 2–4-gram BM25 baseline. The repository research reports character n-gram BM25 as stronger than dense-only retrieval in its Khmer web experiment. This is especially relevant for legal article numbers, names, exact terms, and spelling variants.

Only after measuring the dense and character-BM25 baselines separately should score fusion be tested.

## Bottom line

The current system is a valid BGE-M3 semantic baseline, but its 0.80 MRR@3 and 0.80 nDCG@3 are not yet a reliable full-system score because only five queries are eligible. The most important immediate work is not a new model: it is a valid legal benchmark, a chunk-size ablation, preservation of Khmer structural punctuation, and explicit handling of Khmer character/spelling variation.

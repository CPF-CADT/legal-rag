# LegalRAG

## Legal Document Search and Question-Answering System

LegalRAG is a proposed legal information retrieval and question-answering system for Cambodian law. It will help users find relevant legal documents, explore individual articles, and receive concise answers grounded in retrieved legal sources.

## Problem

Cambodian legal information can be difficult to search manually because documents are distributed across a large digital collection and may contain lengthy or scanned text. Users need a faster way to locate relevant articles and verify the original source.

## Proposed Solution

LegalRAG will combine document collection, text extraction, legal-article transformation, search, and source-based question answering in one system.

The system will:

- collect legal documents from the NCDD Digital Library;
- extract text from scanned and digital PDF documents;
- transform documents into searchable legal articles;
- retrieve articles relevant to a user's query;
- answer questions using the retrieved legal content; and
- provide references to the original documents for verification.

## Main Features

### Legal Document Search

- Search Cambodian laws using keywords or natural-language queries.
- Retrieve relevant laws and specific legal articles.
- Open the original document and source reference.

### Source-Based Question Answering

- Ask questions about Cambodian laws in natural language.
- Receive answers based on retrieved legal articles.
- View the sources used to prepare each answer.

## Project Objectives

- Improve access to Cambodian legal information.
- Reduce the time needed to search lengthy legal documents.
- Help users locate relevant laws and articles more efficiently.
- Support answers that are traceable to official legal sources.
- Provide a foundation for future legal information tools.

## Target Users

- Students
- Lawyer
- General Citizen
- Reporter

## Project Roadmap

| Phase | Tasks |
| --- | --- |
| 1. Data Collection | Crawl and download legal PDFs from the NCDD Digital Library using responsible scraping practices, including `robots.txt`, rate limits, terms of use, duplicate checks, and crawler limits. |
| 2. Data Processing | Convert PDFs to text with OCR, transform the text into structured CSV files, and clean the resulting data. |
| 3. Index Construction | Tokenize and normalize legal text, handle stop words where appropriate, build postings lists, support Boolean AND, OR, and NOT queries, and construct the lexical indexes required for efficient retrieval. |
| 4. Text Embedding and Vector Storage | Prepare the normalized legal-article text for embedding, select a Khmer-capable embedding model, generate embeddings, and store vectors with article metadata in a vector database. |
| 5. Search Method Testing | Implement and compare TF-IDF, cosine similarity, BM25, dense-vector retrieval, hybrid retrieval with rank fusion, and reranking where appropriate. |
| 6. Question Answering | Build a retrieval-augmented question-answering pipeline with source-grounded answers. |
| 7. User Interface | Develop the React web interface and Telegram bot. |
| 8. Evaluation and Deployment | Create test queries and relevance judgments, evaluate retrieval with Precision, Recall, F1, Precision@K, MAP, and NDCG, analyze answer quality, study PageRank and HITS where applicable, and deploy the system. |

### Evaluation Focus

Evaluation will measure whether the system retrieves relevant legal articles and produces answers supported by cited sources. It will cover:

- retrieval quality for Boolean, TF-IDF, BM25, dense-vector, and hybrid search;
- ranking quality for relevant legal articles;
- Precision, Recall, F1, Precision@K, MAP, and NDCG;
- source coverage and citation correctness; and
- answer usefulness, completeness, and factual consistency.

## Dataset

Legal documents are sourced from the **National Committee for Sub-National Democratic Development (NCDD) Digital Library**.

Source: <https://library.ncdd.gov.kh>

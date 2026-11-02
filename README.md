# LegalRAG

LegalRAG is a legal information retrieval and question-answering system for
Cambodian law. It will help users find relevant legal documents, explore
individual articles, and receive concise answers grounded in retrieved legal
sources.

## 1. Problem

Cambodian legal information can be difficult to search manually because the
documents are distributed across a large digital collection and may contain
lengthy or scanned text. LegalRAG will serve users who need to find and verify
legal information quickly.

The search engine will support keyword and natural-language queries, retrieve
relevant laws and articles, and link each result to its original source. A
source-based question-answering feature will provide concise answers with the
retrieved legal articles as references.

## 2. Corpus

The corpus will focus on Cambodian legal documents, primarily in Khmer, from
the **National Committee for Sub-National Democratic Development (NCDD) Digital
Library**:

- Source: <https://library.ncdd.gov.kh>
- Content: laws and related legal documents
- Language: mainly Khmer
- Current collection : approximately **860 pdf**

For the first version, we will focus on these three selected domains:

1. **ការងារ និងសន្តិសុខសង្គម** — 39 pdf records
2. **កម្មសិទ្ធិបញ្ញា** — 39 pdf records
3. **ពាណិជ្ជកម្ម និងអាជីវកម្ម** — 39 pdf records

## 3. Team roles

- **Phy Vathanak:** Crawling, data preprocess (pdf to text) text embedning,  cleanning, and testing dense retrieval.
- **Sat Panaha and Cheng Chanpanaha:** Data cleaning, Khmer tokenization, and BM25 retrieval.
- **Choun Rothanak and Chhun Siv Heng:** Test with TF-IDF search implementation.
- **All members:** Evaluate the search methods and decide whether to use the best method or a hybrid approach.

## 4. Risks

The main uncertainties are:

- **Text embedding:** available embedding models may not represent Khmer legal
  text accurately.
- **Khmer tokenization:** Khmer word segmentation and normalization may affect
  BM25 and TF-IDF indexing and ranking.
- **OCR quality:** errors in scanned legal documents may produce incomplete or
  incorrect text.
- **Text-generation models:** models may have limited support legal terminology for
  Khmer.

"""Independent numeric, persistence, analyzer-contract, and article-collapse checks."""

from contextlib import redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bm25_index import BM25, BM25Searcher, InvertedIndex, naive_bm25
from text_pipeline import Analyzer


class BM25Tests(unittest.TestCase):
    """Check the requested formula against hand calculations and independent scans."""

    def setUp(self) -> None:
        """Create three short Khmer documents with an average length of two tokens."""
        self.documents = {'d1': ['ច្បាប់', 'ច្បាប់', 'កម្មករ'],
                          'd2': ['ច្បាប់', 'ពាណិជ្ជកម្ម'], 'd3': ['កម្មករ']}
        self.index = InvertedIndex.from_tokens(self.documents)
        self.scorer = BM25(self.index)

    def test_lucene_idf(self) -> None:
        """For N=3 and df=2, IDF must be ln(1.6), including when all documents match."""
        self.assertAlmostEqual(self.scorer.idf('ច្បាប់'), math.log(1.6), places=14)
        all_docs = BM25(InvertedIndex.from_tokens({'a': ['x'], 'b': ['x']}))
        self.assertAlmostEqual(all_docs.idf('x'), math.log(1.2), places=14)
        self.assertGreater(all_docs.idf('x'), 0)

    def test_hand_calculated_corpus(self) -> None:
        """Use independently written constants for the two contributions in document d1."""
        expected = 0.9621424372628560
        actual = self.scorer.score(['ច្បាប់', 'កម្មករ'], 'd1')
        self.assertAlmostEqual(actual, expected, places=13)
        self.assertAlmostEqual(self.scorer.scores(['ច្បាប់', 'កម្មករ'])['d1'], expected, places=13)
        terms = self.scorer.contributions(['ច្បាប់', 'កម្មករ'], 'd1')
        self.assertAlmostEqual(sum(row['partial_score'] for row in terms), actual, places=14)

    def test_naive_all_documents_and_parameters(self) -> None:
        """Compare missing, repeated, and mixed terms under several scoring parameters."""
        queries = [[], ['absent'], ['ច្បាប់'], ['ច្បាប់', 'កម្មករ'], ['ច្បាប់', 'ច្បាប់', 'absent']]
        for k1, b in [(1.5, 0.75), (0.0, 0.0), (2.2, 1.0)]:
            scorer = BM25(self.index, k1=k1, b=b)
            for query in queries:
                fast = scorer.scores(query)
                slow = naive_bm25(self.documents, query, k1=k1, b=b)
                for record_id, expected in slow.items():
                    self.assertAlmostEqual(fast.get(record_id, 0.0), expected, places=12)
        self.assertEqual(self.scorer.scores([]), {})
        self.assertEqual(self.scorer.scores(['absent']), {})
        self.assertAlmostEqual(self.scorer.score(['ច្បាប់', 'ច្បាប់'], 'd1'),
                               2 * self.scorer.score(['ច្បាប់'], 'd1'), places=14)

    def test_empty_corpus_and_documents(self) -> None:
        """Empty indexes and zero-length documents contribute no scores or division errors."""
        for documents in [{}, {'empty': []}, {'empty': [], 'a': ['x']}]:
            scorer = BM25(InvertedIndex.from_tokens(documents))
            fast = scorer.scores(['x'])
            slow = naive_bm25(documents, ['x'])
            for record_id, expected in slow.items():
                self.assertAlmostEqual(fast.get(record_id, 0.0), expected)
        self.assertEqual(BM25(InvertedIndex()).idf('x'), 0.0)

    def test_index_roundtrip_and_raw_compatibility(self) -> None:
        """Token indexes round-trip while raw indexes preserve longest-text ID handling."""
        raw = InvertedIndex.build([{'article_id': 'a', 'text': 'one'}, {'article_id': 'a', 'text': 'one two'}])
        self.assertEqual(raw.document_lengths, {'a': 2})
        for index in [raw, self.index]:
            with TemporaryDirectory() as directory:
                index.save(Path(directory))
                reloaded = InvertedIndex.load(Path(directory))
                self.assertEqual(index.tokenization, reloaded.tokenization)
                self.assertEqual(index.postings, reloaded.postings)
                self.assertEqual(index.document_lengths, reloaded.document_lengths)
        for tokens in [[''], ['two words'], [1]]:
            with self.assertRaises(ValueError):
                InvertedIndex.from_tokens({'bad': tokens})

    def test_parameter_validation(self) -> None:
        """Reject parameters that would make scoring invalid or nonsensical."""
        for k1, b in [(-1, 0.75), (math.inf, 0.75), (math.nan, 0.75), (1.5, -0.1), (1.5, 1.1)]:
            with self.assertRaises(ValueError):
                BM25(self.index, k1=k1, b=b)


class BM25SearcherTests(unittest.TestCase):
    """Check durable analyzer matching and best-record article results."""

    def setUp(self) -> None:
        """Build a verified fixture containing two records with the same article ID."""
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.config_path = self.folder / 'preprocess_config.json'
        self.index_dir = self.folder / 'index'
        self.analyzer = Analyzer(tokenizer='syllable_ngrams')
        self.analyzer.save_config(self.config_path)
        articles = [{'article_id': 'same', 'text': 'law filler filler filler filler', 'document_title': 'long'},
                    {'article_id': 'same', 'text': 'law law', 'document_title': 'short'},
                    {'article_id': 'other', 'text': 'trade'}]
        token_records = [{'article_id': row['article_id'], 'source_record_index': position,
                          'tokens': self.analyzer.analyze_document(row)} for position, row in enumerate(articles)]
        self.articles_path = self.folder / 'articles.jsonl'
        self.tokens_path = self.folder / 'articles_tokens.jsonl'
        for path, rows in [(self.articles_path, articles), (self.tokens_path, token_records)]:
            path.write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
        BM25Searcher.build_index(self.tokens_path, self.articles_path, self.config_path, self.index_dir)
        self.searcher = BM25Searcher(self.index_dir, self.config_path)

    def test_best_record_and_exact_result_shape(self) -> None:
        """Keep the best duplicate's text and metadata instead of summing its scores."""
        results = self.searcher.search('law')
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['article_id'], 'same')
        self.assertEqual(result['full_article'], 'law law')
        self.assertEqual(result['title'], 'short')
        self.assertEqual(result['matched_terms'], ['law'])
        self.assertEqual(set(result), {'rank', 'article_id', 'title', 'document_id', 'article_number',
                                      'full_article', 'matched_chunks', 'source_url', 'pdf_url', 'score', 'matched_terms'})
        self.assertEqual(set(result['matched_chunks'][0]), {'chunk_id', 'chunk_text', 'distance'})
        self.assertIsNone(result['matched_chunks'][0]['distance'])
        expected = self.searcher.scorer.scores(['law'])
        self.assertEqual(result['score'], max(expected.values()))
        self.assertEqual(self.searcher.index.total_documents, 3)

    def test_search_edges_and_explanation(self) -> None:
        """Empty, stopword-only, and unknown queries return no results; explanations sum."""
        for query in ['', 'និង', 'absentword']:
            self.assertEqual(self.searcher.search(query), [])
        self.assertEqual(self.searcher.search('law', top_k=0), [])
        with self.assertRaises(ValueError):
            self.searcher.search('law', top_k=-1)
        with redirect_stdout(StringIO()):
            explained = self.searcher.explain('law law absentword', 'same')
        self.assertAlmostEqual(sum(row['partial_score'] for row in explained['terms']), explained['score'])
        self.assertEqual(explained['terms'][0]['query_frequency'], 2)
        self.assertEqual(explained['terms'][1]['tf'], 0)
        with self.assertRaises(KeyError):
            self.searcher.explain('law', 'missing-id')

    def test_query_and_manifest_mismatch(self) -> None:
        """Reject query drift both at load time and after constructing a searcher."""
        incompatible = Analyzer(tokenizer='syllable_ngrams', include_context=True)
        with self.assertRaisesRegex(ValueError, 'Analyzer configuration mismatch'):
            BM25Searcher(self.index_dir, self.config_path, analyzer=incompatible)
        self.searcher.analyzer.include_context = True
        with self.assertRaisesRegex(ValueError, 'Analyzer configuration mismatch'):
            self.searcher.search('law')
        manifest_path = self.index_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['analyzer_config']['INCLUDE_CONTEXT'] = True
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Index manifest analyzer settings differ'):
            BM25Searcher(self.index_dir, self.config_path)

    def test_artifact_integrity_and_parameter_independence(self) -> None:
        """Change scoring parameters without rebuilding, and reject altered index files."""
        alternate = BM25Searcher(self.index_dir, self.config_path, k1=2.0, b=0.3)
        self.assertEqual(alternate.index.postings, self.searcher.index.postings)
        self.assertNotEqual(alternate.search('law')[0]['score'], self.searcher.search('law')[0]['score'])
        self.assertNotIn('k1', self.searcher.manifest)
        self.assertNotIn('b', self.searcher.manifest)
        path = self.index_dir / 'index.json'
        path.write_text(path.read_text() + '\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'artifact does not match manifest'):
            BM25Searcher(self.index_dir, self.config_path)

    def test_misaligned_input_is_rejected(self) -> None:
        """Do not attach tokens to a raw record with a different canonical article ID."""
        tokens = [json.loads(line) for line in self.tokens_path.read_text().splitlines()]
        tokens[0]['article_id'] = 'wrong'
        self.tokens_path.write_text('\n'.join(json.dumps(row) for row in tokens), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'mismatched canonical article ID'):
            BM25Searcher.build_index(self.tokens_path, self.articles_path, self.config_path, self.index_dir)


if __name__ == '__main__':
    unittest.main()

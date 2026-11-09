"""Regression checks for shared analysis, exact normalization, and config refusal."""

import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from text_pipeline import (Analyzer, fold_digits, normalization_report, normalize_khmer,
                           selected_record_indices, strip_punctuation)


class TextPipelineTests(unittest.TestCase):
    """Check behaviors that future BM25 query and document processing must share."""

    def test_normalizer_is_verbatim(self) -> None:
        """Keep both functions and constants identical to the teammate notebook."""
        folder = Path(__file__).resolve().parent
        notebook = json.loads((folder.parent / 'notebooks' / '05_normalize_articles.ipynb').read_text())
        names = {'normalize_khmer', 'normalize_khmer_cluster_order', 'ZERO_WIDTH', 'SPELLING_VARIANTS'}
        originals = {}
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code':
                continue
            source = ''.join(cell['source'])
            for node in ast.parse(source).body:
                if isinstance(node, ast.FunctionDef) and node.name in names:
                    originals[node.name] = ast.get_source_segment(source, node)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in names:
                            originals[target.id] = ast.get_source_segment(source, node)
        source = (folder / 'text_pipeline.py').read_text()
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name in originals:
                self.assertEqual(ast.get_source_segment(source, node), originals.pop(node.name))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in originals:
                        self.assertEqual(ast.get_source_segment(source, node), originals.pop(target.id))
        self.assertFalse(originals)

    def test_digit_and_punctuation_boundaries(self) -> None:
        """Separate adjacent digits without erasing legal word boundaries or Khmer marks."""
        self.assertEqual(fold_digits('ឆ្នាំ២០១៥abc១២ខ្មែរ'), 'ឆ្នាំ 2015 abc 12 ខ្មែរ')
        self.assertEqual(strip_punctuation('ច្បាប់។ខ្មែរ៕៖ + $'), 'ច្បាប់ ខ្មែរ      ')
        analyzer = Analyzer()
        tokens = analyzer.analyze('មាត្រា១២ ABC២៣ ត្រូវ មិន ហាម អាច ឬ សិទ្ធិ កាតព្វកិច្ច')
        self.assertIn('12', tokens)
        self.assertIn('abc', tokens)
        self.assertIn('23', tokens)
        for word in ['ត្រូវ', 'មិន', 'ហាម', 'អាច', 'ឬ', 'សិទ្ធិ', 'កាតព្វកិច្ច']:
            self.assertIn(word, tokens)
        self.assertEqual(analyzer.analyze(''), [])
        self.assertEqual(analyzer.analyze('។៕៖+$'), [])
        self.assertNotIn('និង', analyzer.analyze('និង'))

    def test_document_query_parity_and_context(self) -> None:
        """Documents and queries use one path, with optional context before analysis."""
        article = {'article_id': 'a', 'document_title': 'unknown', 'article_number': 12,
                   'text': 'ប្រជាពលរដ្ឋត្រូវគោរពច្បាប់។'}
        for include_context in [False, True]:
            analyzer = Analyzer(include_context=include_context)
            self.assertEqual(analyzer.analyze_document(article),
                             analyzer.analyze(analyzer.document_text(article)))
            self.assertEqual(analyzer.explain(analyzer.document_text(article))['6. Stopwords removed'],
                             analyzer.analyze_document(article))
        self.assertIn('unknown', Analyzer(include_context=True).analyze_document(article))
        self.assertEqual(Analyzer(include_context=True).document_text({'text': 'ច្បាប់'}), 'ច្បាប់')

    def test_configuration_refuses_drift(self) -> None:
        """Reject context, tokenizer, stopword, code, version, and unknown-key drift."""
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            analyzer = Analyzer()
            analyzer.save_config(path)
            self.assertEqual(Analyzer.from_config(path).config(), analyzer.config())
            for other in [Analyzer(include_context=True), Analyzer(tokenizer='syllable_ngrams')]:
                with self.assertRaises(ValueError):
                    other.assert_compatible(path)
            stopwords = Path(directory) / 'words.txt'
            stopwords.write_text('ត្រូវ\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                Analyzer.from_config(path, stopword_path=stopwords)
            for key, value in [('pipeline_sha256', 'changed'), ('package_versions', {}), ('extra', None)]:
                altered = dict(analyzer.config())
                altered[key] = value
                path.write_text(json.dumps(altered), encoding='utf-8')
                with self.assertRaises(ValueError):
                    analyzer.assert_compatible(path)

    def test_normalization_reference_checks_all_records(self) -> None:
        """Check repeated IDs separately and report missing, changed, or extra records."""
        rows = [{'article_id': 'a', 'text': 'ឆ្នាំ\u200b១២'}, {'article_id': 'a', 'text': 'ច្បាប់'}]
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'reference.jsonl'
            self.assertFalse(normalization_report(rows, path)['available'])
            dense = [dict(row, search_text=normalize_khmer(row['text'])) for row in rows]
            path.write_text('\n'.join(json.dumps(row) for row in dense), encoding='utf-8')
            self.assertEqual(normalization_report(rows, path)['matches'], 2)
            dense[1]['search_text'] = 'wrong'
            path.write_text('\n'.join(json.dumps(row) for row in dense), encoding='utf-8')
            self.assertEqual(normalization_report(rows, path)['mismatches'], 1)
            self.assertEqual(normalization_report(rows[:1], path)['mismatches'], 1)

    def test_comparison_selects_same_raw_records(self) -> None:
        """Retain longest texts, first ties, empty articles, and canonical fallback IDs."""
        rows = [{'article_id': 'a', 'text': 'a'}, {'article_id': 'a', 'text': 'aa'},
                {'article_id': 'a', 'text': 'bb'}, {'document_id': 'b', 'article_number': 2, 'text': ''}]
        self.assertEqual(selected_record_indices(rows), [1, 3])

    def test_syllable_alternative_preserves_runs(self) -> None:
        """Keep Latin/digit tokens whole and avoid n-grams across whitespace boundaries."""
        analyzer = Analyzer(tokenizer='syllable_ngrams', syllable_ngram_min=1, syllable_ngram_max=2)
        self.assertEqual(analyzer.analyze('ក ខ ABC១២'), ['ក', 'ខ', 'abc', '12'])
        self.assertEqual(analyzer.analyze('កខ'), ['ក', 'ខ', 'កខ'])
        with self.assertRaises(ValueError):
            Analyzer(tokenizer='unknown')
        with self.assertRaises(ValueError):
            Analyzer(syllable_ngram_min=2, syllable_ngram_max=1)


if __name__ == '__main__':
    unittest.main()

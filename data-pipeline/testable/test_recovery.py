"""Recovery tests for the sequential CSV-based pipeline."""

import asyncio
import logging
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data-pipeline" / "data"
sys.path.insert(0, str(PROJECT_ROOT / "data-pipeline" / "automation-process" / "download"))
sys.path.insert(0, str(PROJECT_ROOT / "data-pipeline" / "automation-process" / "ocr"))

from downloader import download_pdf  # noqa: E402
from processor import process_document  # noqa: E402
from scraper import load_documents, process_record, save_documents  # noqa: E402


SAMPLE_PDF = DATA_DIR / "temp" / "ncdd_laws" / "pdfs" / "16764.pdf"


class FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/pdf"):
        self.body = body
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, _chunk_size):
        yield self.body


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, *_args, **_kwargs):
        return self.response


class FakeKeyManager:
    def next_key(self):
        return "key-001", "fake-key"

    def record_success(self, _key_id):
        return None

    def record_error(self, _key_id, _error):
        return "transient"


class FakeGeminiClient:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = 0

    def extract_chunk(self, _chunk_path, _prompt):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("temporary Gemini failure")
        return "ខ្លឹមសារសាកល្បង", {"total_tokens": 1}


def ocr_settings(root: Path) -> dict:
    return {
        "chunks_dir": root / "chunks",
        "chunk_text_dir": root / "chunk_text",
        "usage_dir": root / "usage",
        "text_dir": root / "text",
        "ocr_batches_checkpoint": root / "ocr_batches.csv",
        "batch_size": 10,
        "max_retries": 2,
        "cooldown_seconds": 0,
        "key_rotation_wait_seconds": 0,
        "model": "test-model",
        "max_gemini_requests": None,
    }


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("recovery-tests")
        self.logger.addHandler(logging.NullHandler())

    def test_download_checkpoint_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            checkpoint = Path(folder) / "documents.csv"
            documents = {
                "123": {
                    "document_id": "123",
                    "title": "Test",
                    "status": "downloaded",
                    "local_pdf_path": "/tmp/123.pdf",
                }
            }
            save_documents(checkpoint, documents)
            restored = load_documents(checkpoint)
            self.assertEqual(restored["123"]["status"], "downloaded")
            self.assertFalse(checkpoint.with_suffix(".csv.tmp").exists())

    def test_invalid_download_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "document.pdf"
            session = FakeSession(FakeResponse(b"not a pdf", "application/octet-stream"))
            with self.assertRaises(ValueError):
                download_pdf(session, "https://example.test/document", destination, "https://example.test", (1, 1))
            self.assertFalse(destination.exists())
            self.assertFalse(destination.with_suffix(".pdf.part").exists())

    def test_existing_valid_pdf_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "123.pdf"
            destination.write_bytes(SAMPLE_PDF.read_bytes())
            record = {"document_id": "123", "detail_url": "https://example.test/detail/123"}
            settings = {"pdf_dir": Path(folder)}
            asyncio.run(process_record(record, None, None, settings, self.logger))
            self.assertEqual(record["status"], "downloaded")

    def test_ocr_retries_and_then_completes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = ocr_settings(root)
            client = FakeGeminiClient(failures=1)
            batches = {}
            process_document(
                SAMPLE_PDF,
                settings,
                batches,
                FakeKeyManager(),
                {"key-001": client},
                "test prompt",
                self.logger,
                [0],
            )
            self.assertEqual(client.calls, 3)
            self.assertTrue((root / "text" / "16764.txt").exists())
            self.assertTrue(all(row["status"] == "completed" for row in batches.values()))

    def test_completed_ocr_batches_are_skipped_on_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = ocr_settings(root)
            batches = {}
            first_client = FakeGeminiClient()
            process_document(
                SAMPLE_PDF,
                settings,
                batches,
                FakeKeyManager(),
                {"key-001": first_client},
                "test prompt",
                self.logger,
                [0],
            )
            second_client = FakeGeminiClient()
            process_document(
                SAMPLE_PDF,
                settings,
                batches,
                FakeKeyManager(),
                {"key-001": second_client},
                "test prompt",
                self.logger,
                [0],
            )
            self.assertEqual(second_client.calls, 0)

    def test_local_mode_limits_gemini_requests_to_two(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = ocr_settings(root)
            settings["max_gemini_requests"] = 2
            client = FakeGeminiClient()
            batches = {}
            requests_used = [0]
            process_document(
                SAMPLE_PDF,
                settings,
                batches,
                FakeKeyManager(),
                {"key-001": client},
                "test prompt",
                self.logger,
                requests_used,
            )
            self.assertEqual(requests_used[0], 2)
            self.assertEqual(client.calls, 2)


if __name__ == "__main__":
    unittest.main()

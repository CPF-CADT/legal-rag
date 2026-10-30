from pathlib import Path


# Direct configuration: edit these values in this file.
OCR_BATCH_SIZE = 10
GEMINI_MODEL = "gemini-3.6-flash"
MAX_RETRIES = 4
COOLDOWN_SECONDS = 60
KEY_ROTATION_WAIT_SECONDS = 60
KEYS_FILE_NAME = "keys.txt"

# Local smoke-test safety limits. Keep disabled for the full pipeline.
LOCAL_TEST_MODE = False
# Empty means: process the first downloaded document from documents.csv.
LOCAL_TEST_DOCUMENT_ID = ""
MAX_GEMINI_REQUESTS = 2


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data-pipeline" / "data"
PDF_DIR = DATA_DIR / "pdfs"
OCR_DIR = DATA_DIR / "ocr"
CHUNKS_DIR = OCR_DIR / "chunks"
CHUNK_TEXT_DIR = OCR_DIR / "chunk_text"
TEXT_DIR = OCR_DIR / "text"
USAGE_DIR = OCR_DIR / "usage"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
LOG_DIR = DATA_DIR / "logs"

KEYS_PATH = PROJECT_ROOT / KEYS_FILE_NAME
DOCUMENTS_CHECKPOINT = CHECKPOINT_DIR / "documents.csv"
OCR_BATCHES_CHECKPOINT = CHECKPOINT_DIR / "ocr_batches.csv"
API_KEYS_CHECKPOINT = CHECKPOINT_DIR / "api_keys.csv"
LOG_PATH = LOG_DIR / "ocr.log"


def ensure_directories() -> None:
    """Create directories required by the OCR processor."""

    for directory in (
        PDF_DIR,
        CHUNKS_DIR,
        CHUNK_TEXT_DIR,
        TEXT_DIR,
        USAGE_DIR,
        CHECKPOINT_DIR,
        LOG_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_directories()
    from processor import run_pipeline

    run_pipeline(
        {
            "project_root": PROJECT_ROOT,
            "pdf_dir": PDF_DIR,
            "chunks_dir": CHUNKS_DIR,
            "chunk_text_dir": CHUNK_TEXT_DIR,
            "text_dir": TEXT_DIR,
            "usage_dir": USAGE_DIR,
            "documents_checkpoint": DOCUMENTS_CHECKPOINT,
            "ocr_batches_checkpoint": OCR_BATCHES_CHECKPOINT,
            "keys_path": KEYS_PATH,
            "api_keys_checkpoint": API_KEYS_CHECKPOINT,
            "log_path": LOG_PATH,
            "batch_size": OCR_BATCH_SIZE,
            "model": GEMINI_MODEL,
            "max_retries": MAX_RETRIES,
            "cooldown_seconds": COOLDOWN_SECONDS,
            "key_rotation_wait_seconds": KEY_ROTATION_WAIT_SECONDS,
            "local_test_mode": LOCAL_TEST_MODE,
            "local_test_document_id": LOCAL_TEST_DOCUMENT_ID,
            "max_gemini_requests": MAX_GEMINI_REQUESTS if LOCAL_TEST_MODE else None,
        }
    )


if __name__ == "__main__":
    main()

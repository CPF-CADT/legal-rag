from pathlib import Path


# Direct configuration: edit these values in this file.
BASE_URL = "https://library.ncdd.gov.kh"
CATEGORY_ID = 7
CATEGORY_NAME = "NCDD Laws"
PER_PAGE = 12
REQUEST_DELAY_SECONDS = 2.0
MAX_RETRIES = 3
# Full pipeline mode. Set True only for a limited local smoke test.
TEST_MODE = False
TEST_PAGES = 2
# Empty means: use the first discovered document for the local smoke test.
TEST_DOCUMENT_ID = ""
TEST_MAX_DOCUMENTS = 1


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data-pipeline" / "data"
PDF_DIR = DATA_DIR / "pdfs"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
LOG_DIR = DATA_DIR / "logs"

DOCUMENTS_CHECKPOINT = CHECKPOINT_DIR / "documents.csv"
LOG_PATH = LOG_DIR / "scraper.log"

USER_AGENT = "LegalRAG NCDD research downloader (respectful rate limits)"
REQUEST_TIMEOUT = (20, 120)


def get_settings() -> dict:
    """Return the scraper configuration used by the other modules."""

    return {
        "base_url": BASE_URL,
        "category_id": CATEGORY_ID,
        "category_name": CATEGORY_NAME,
        "per_page": PER_PAGE,
        "request_delay_seconds": REQUEST_DELAY_SECONDS,
        "max_retries": MAX_RETRIES,
        "test_mode": TEST_MODE,
        "test_pages": TEST_PAGES,
        "test_document_id": TEST_DOCUMENT_ID,
        "test_max_documents": TEST_MAX_DOCUMENTS,
        "pdf_dir": PDF_DIR,
        "checkpoint_path": DOCUMENTS_CHECKPOINT,
        "log_path": LOG_PATH,
        "user_agent": USER_AGENT,
        "request_timeout": REQUEST_TIMEOUT,
    }


def ensure_directories() -> None:
    """Create directories required by the scraper."""

    for directory in (PDF_DIR, CHECKPOINT_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_directories()
    from scraper import run_pipeline

    run_pipeline(get_settings())


if __name__ == "__main__":
    main()

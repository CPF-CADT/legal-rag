import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz

from gemini_client import GeminiClient
from key_manager import KeyManager, NoUsableKeyError


PROMPT_PATH = Path(__file__).resolve().parents[1] / "PROMT.md"
BATCH_FIELDS = [
    "batch_id",
    "document_id",
    "batch_number",
    "page_start",
    "page_end",
    "chunk_path",
    "text_path",
    "status",
    "retry_count",
    "api_key_id",
    "error",
    "updated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_csv(path: Path, key_field: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row[key_field]: row
            for row in csv.DictReader(file)
            if row.get(key_field)
        }


def save_batches(path: Path, batches: dict[str, dict]) -> None:
    """Atomically save OCR batch checkpoint rows."""

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=BATCH_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in BATCH_FIELDS}
            for row in sorted(batches.values(), key=lambda item: item["batch_id"])
        )
    temporary.replace(path)


def batch_id(document_id: str, number: int) -> str:
    return f"{document_id}:{number}"


def split_pdf(pdf_path: Path, chunks_root: Path, batch_size: int) -> list[dict]:
    """Create deterministic PDF chunks and return their page metadata."""

    document_id = pdf_path.stem
    document_dir = chunks_root / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    batches = []
    with fitz.open(pdf_path) as source:
        for start in range(0, source.page_count, batch_size):
            end = min(start + batch_size, source.page_count)
            number = start // batch_size + 1
            chunk_path = document_dir / f"{document_id}-{number}.pdf"
            if not chunk_path.exists():
                chunk = fitz.open()
                chunk.insert_pdf(source, from_page=start, to_page=end - 1)
                temporary = chunk_path.with_suffix(".pdf.tmp")
                chunk.save(temporary)
                chunk.close()
                temporary.replace(chunk_path)
            batches.append(
                {
                    "batch_id": batch_id(document_id, number),
                    "document_id": document_id,
                    "batch_number": str(number),
                    "page_start": str(start + 1),
                    "page_end": str(end),
                    "chunk_path": str(chunk_path),
                }
            )
    return batches


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def write_usage(path: Path, document_id: str, batch: dict, usage: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "document_id": document_id,
        "batch": batch["batch_id"],
        "page_start": batch["page_start"],
        "page_end": batch["page_end"],
        **usage,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def remove_failed_outputs(text_path: Path, usage_path: Path) -> None:
    """Remove outputs when a batch did not finish as one complete unit."""

    text_path.unlink(missing_ok=True)
    usage_path.unlink(missing_ok=True)


def process_document(
    pdf_path: Path,
    settings: dict,
    batches: dict[str, dict],
    key_manager: KeyManager,
    clients: dict[str, GeminiClient],
    prompt: str,
    logger: logging.Logger,
    requests_used: list[int],
    last_request_at: list[float | None] | None = None,
) -> None:
    if last_request_at is None:
        last_request_at = [None]
    document_id = pdf_path.stem
    chunk_batches = split_pdf(pdf_path, settings["chunks_dir"], settings["batch_size"])
    document_text_dir = settings["chunk_text_dir"] / document_id
    document_usage_dir = settings["usage_dir"] / document_id
    document_text_dir.mkdir(parents=True, exist_ok=True)
    document_usage_dir.mkdir(parents=True, exist_ok=True)

    for batch in chunk_batches:
        number = batch["batch_number"]
        text_path = document_text_dir / f"{document_id}-{number}.txt"
        usage_path = document_usage_dir / f"{document_id}-{number}.json"
        checkpoint = batches.get(batch["batch_id"], {})
        row = {**checkpoint, **batch, "text_path": str(text_path)}

        if checkpoint.get("status") == "completed" and text_path.exists() and text_path.stat().st_size > 0:
            batches[batch["batch_id"]] = row
            continue

        row.update(status="processing", error="", updated_at=now_utc())
        batches[batch["batch_id"]] = row
        save_batches(settings["ocr_batches_checkpoint"], batches)

        for attempt in range(settings["max_retries"]):
            row["retry_count"] = str(attempt + 1)
            key_id = ""
            try:
                request_limit = settings.get("max_gemini_requests")
                if request_limit is not None and requests_used[0] >= request_limit:
                    row.update(
                        status="pending",
                        error="Local test Gemini request limit reached",
                        updated_at=now_utc(),
                    )
                    batches[batch["batch_id"]] = row
                    save_batches(settings["ocr_batches_checkpoint"], batches)
                    logger.info("Local test limit reached after %s Gemini requests", requests_used[0])
                    return
                key_id, key_value = key_manager.next_key()
                row["api_key_id"] = key_id
                client = clients.get(key_id)
                if client is None:
                    client = GeminiClient(key_value, settings["model"])
                    clients[key_id] = client
                started = time.perf_counter()
                if last_request_at[0] is not None:
                    elapsed = time.monotonic() - last_request_at[0]
                    wait_seconds = settings["cooldown_seconds"] - elapsed
                    if wait_seconds > 0:
                        logger.info("Waiting %.1f seconds before the next Gemini request", wait_seconds)
                        time.sleep(wait_seconds)
                requests_used[0] += 1
                last_request_at[0] = time.monotonic()
                text, usage = client.extract_chunk(Path(batch["chunk_path"]), prompt)
                try:
                    write_text_atomic(text_path, text)
                    write_usage(usage_path, document_id, batch, usage)
                except Exception:
                    remove_failed_outputs(text_path, usage_path)
                    raise
                key_manager.record_success(key_id)
                row.update(status="completed", error="", updated_at=now_utc())
                batches[batch["batch_id"]] = row
                save_batches(settings["ocr_batches_checkpoint"], batches)
                logger.info(
                    "%s batch %s completed in %.2fs",
                    document_id,
                    number,
                    time.perf_counter() - started,
                )
                break
            except NoUsableKeyError as error:
                row.update(status="failed", error=str(error), updated_at=now_utc())
                batches[batch["batch_id"]] = row
                save_batches(settings["ocr_batches_checkpoint"], batches)
                logger.error("OCR stopped: %s", error)
                return
            except Exception as error:
                category = key_manager.record_error(key_id, error) if key_id else "transient"
                row.update(status="failed", error=str(error)[-2000:], updated_at=now_utc())
                batches[batch["batch_id"]] = row
                save_batches(settings["ocr_batches_checkpoint"], batches)
                logger.warning(
                    "%s batch %s attempt %s failed: %s",
                    document_id,
                    number,
                    attempt + 1,
                    f"{category}: {error}",
                )
                if attempt < settings["max_retries"] - 1:
                    time.sleep(settings["key_rotation_wait_seconds"])

        if batches[batch["batch_id"]].get("status") != "completed":
            logger.error("Stopping document %s because batch %s failed", document_id, number)
            return

    final_path = settings["text_dir"] / f"{document_id}.txt"
    parts = []
    for batch in chunk_batches:
        row = batches[batch["batch_id"]]
        text_path = Path(row["text_path"])
        if row.get("status") != "completed" or not text_path.exists():
            logger.warning("Final text skipped for incomplete document %s", document_id)
            return
        parts.append(text_path.read_text(encoding="utf-8").strip())
    write_text_atomic(final_path, "\n\n".join(parts))
    logger.info("Final text created: %s", final_path)


def build_logger(path: Path) -> logging.Logger:
    logger = logging.getLogger("ncdd_ocr")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger


def run_pipeline(settings: dict) -> None:
    logger = build_logger(settings["log_path"])
    key_manager = KeyManager(
        settings["keys_path"],
        settings["api_keys_checkpoint"],
        settings["cooldown_seconds"],
    )
    clients = {}
    prompt = load_prompt()
    documents = load_csv(settings["documents_checkpoint"], "document_id")
    batches = load_csv(settings["ocr_batches_checkpoint"], "batch_id")

    downloaded = [
        row for row in documents.values()
        if row.get("status") == "downloaded"
    ]
    if not downloaded:
        logger.info("No downloaded documents found")
        return

    if settings.get("local_test_mode"):
        document_id = settings["local_test_document_id"]
        if document_id:
            downloaded = [row for row in downloaded if row.get("document_id") == document_id]
        else:
            downloaded = downloaded[:1]
        logger.info(
            "Local test mode: document=%s; maximum Gemini requests=%s",
            document_id or (downloaded[0]["document_id"] if downloaded else "none"),
            settings["max_gemini_requests"],
        )

    requests_used = [0]
    last_request_at = [None]
    for document in sorted(downloaded, key=lambda row: row["document_id"]):
        pdf_path = Path(document.get("local_pdf_path") or "")
        if not pdf_path.exists():
            logger.warning("Missing PDF for document %s: %s", document["document_id"], pdf_path)
            continue
        process_document(
            pdf_path,
            settings,
            batches,
            key_manager,
            clients,
            prompt,
            logger,
            requests_used,
            last_request_at,
        )

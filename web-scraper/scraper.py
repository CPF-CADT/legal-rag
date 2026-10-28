import asyncio
import csv
import logging
import random
import re
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from downloader import candidates_from_html, download_pdf, valid_pdf


DOCUMENT_FIELDS = [
    "document_id",
    "title",
    "detail_url",
    "pdf_url",
    "local_pdf_path",
    "status",
    "retry_count",
    "error",
    "document_type",
    "publication_date",
    "publication_year",
    "language",
    "category",
    "category_id",
    "updated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_documents(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row["document_id"]: row
            for row in csv.DictReader(file)
            if row.get("document_id")
        }


def save_documents(path: Path, documents: dict[str, dict]) -> None:
    """Atomically save the current document checkpoint."""

    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=DOCUMENT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            {field: record.get(field, "") for field in DOCUMENT_FIELDS}
            for record in sorted(documents.values(), key=lambda item: item["document_id"])
        )
    temporary.replace(path)


def listing_url(settings: dict, page_number: int) -> str:
    return (
        f"{settings['base_url']}/product?category={settings['category_id']}"
        f"&page={page_number}&perpage={settings['per_page']}"
    )


async def pause(settings: dict) -> None:
    delay = settings["request_delay_seconds"]
    await asyncio.sleep(delay + random.uniform(0, 0.5))


async def fetch_page(page, url: str) -> BeautifulSoup:
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(1200)
    return BeautifulSoup(await page.content(), "html.parser")


async def open_browser(playwright):
    """Open a fresh browser and page for recovery after a browser crash."""

    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    return browser, page


def parse_records(soup: BeautifulSoup, page_number: int, base_url: str) -> dict[str, dict]:
    records = {}
    for link in soup.select("a[href]"):
        href = urljoin(base_url, link.get("href", ""))
        match = re.search(r"/detail/(\d+)(?:[/?#]|$)", href)
        if not match:
            continue
        document_id = match.group(1)
        title = link.get_text(" ", strip=True)
        record = {
            "document_id": document_id,
            "title": title,
            "detail_url": href,
            "category_id": str(page_number),
            "status": "discovered",
            "retry_count": "0",
            "updated_at": now_utc(),
        }
        if document_id not in records or len(title) > len(records[document_id]["title"]):
            records[document_id] = record
    return records


def get_total(soup: BeautifulSoup) -> int | None:
    text = soup.get_text(" ", strip=True)
    for pattern in (r"of\s+([\d,]+)\s+records", r"([\d,]+)\s+records", r"ចំនួន\s*([\d,]+)"):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def get_last_page(soup: BeautifulSoup, base_url: str) -> int | None:
    numbers = []
    for link in soup.select("a[href]"):
        query = parse_qs(urlparse(urljoin(base_url, link.get("href", ""))).query)
        if "page" in query and query["page"][0].isdigit():
            numbers.append(int(query["page"][0]))
    return max(numbers) if numbers else None


def khmer_digits_to_latin(value: str) -> str:
    return value.translate(str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789"))


def infer_document_type(title: str) -> str | None:
    types = (
        ("ច្បាប់", "Law"),
        ("ព្រះរាជក្រម", "Royal Kram"),
        ("ព្រះរាជក្រឹត្យ", "Royal Decree"),
        ("អនុក្រឹត្យ", "Sub-decree"),
        ("ប្រកាស", "Prakas"),
        ("សេចក្តីសម្រេច", "Decision"),
        ("សារាចរ", "Circular"),
    )
    for marker, document_type in types:
        if marker in title:
            return document_type
    return None


def extract_metadata(soup: BeautifulSoup, record: dict, settings: dict) -> None:
    title = record.get("title", "").strip()
    page_text = soup.get_text(" ", strip=True)
    combined_text = khmer_digits_to_latin(f"{title} {page_text}")
    title_normalized = khmer_digits_to_latin(title)
    years = re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", title_normalized)
    if not years:
        years = re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", combined_text)
    date_pattern = r"(?:ថ្ងៃទី|dated|date)\s*([0-9]{1,2}[^0-9]{1,3}[0-9]{1,2}[^0-9]{1,3}(?:19|20)\d{2})"
    date_match = re.search(date_pattern, title_normalized, re.IGNORECASE) or re.search(
        date_pattern, combined_text, re.IGNORECASE
    )
    record.update(
        {
            "document_type": infer_document_type(title),
            "publication_year": years[-1] if years else "",
            "publication_date": date_match.group(1) if date_match else "",
            "language": "Khmer",
            "category_id": str(settings["category_id"]),
            "category": settings["category_name"],
            "updated_at": now_utc(),
        }
    )


async def discover_records(settings: dict, documents: dict[str, dict], logger) -> None:
    failed_pages = []
    async with async_playwright() as playwright:
        browser, page = await open_browser(playwright)
        try:
            first = await fetch_page(page, listing_url(settings, 1))
            expected = get_total(first)
            last_page = get_last_page(first, settings["base_url"])
            if expected is not None:
                total_pages = ceil(expected / settings["per_page"])
            elif last_page is not None:
                total_pages = last_page
            else:
                raise RuntimeError("Could not determine NCDD page count")
            if settings["test_mode"]:
                total_pages = min(settings["test_pages"], total_pages)

            logger.info("Reported records=%s; pages=%s", expected, total_pages)
            for page_number in range(1, total_pages + 1):
                for attempt in range(settings["max_retries"]):
                    try:
                        soup = first if page_number == 1 else await fetch_page(
                            page, listing_url(settings, page_number)
                        )
                        found = parse_records(soup, page_number, settings["base_url"])
                        if not found:
                            raise RuntimeError("No detail links found")
                        for document_id, record in found.items():
                            existing = documents.get(document_id, {})
                            record.update(
                                {
                                    key: existing[key]
                                    for key in ("status", "retry_count", "error", "pdf_url", "local_pdf_path")
                                    if existing.get(key)
                                }
                            )
                            documents[document_id] = {**existing, **record, "updated_at": now_utc()}
                        save_documents(settings["checkpoint_path"], documents)
                        logger.info("Discovered page %s: %s records", page_number, len(found))
                        break
                    except Exception as error:
                        logger.warning(
                            "Page %s attempt %s failed: %s",
                            page_number,
                            attempt + 1,
                            error,
                        )
                        if "Target page, context or browser has been closed" in str(error):
                            logger.warning("Playwright browser closed; restarting it before retry")
                            try:
                                await browser.close()
                            except Exception:
                                pass
                            browser, page = await open_browser(playwright)
                        if attempt == settings["max_retries"] - 1:
                            logger.error("Giving up on listing page %s", page_number)
                            failed_pages.append(page_number)
                        else:
                            await pause(settings)
                await pause(settings)
        finally:
            await browser.close()
    if failed_pages:
        raise RuntimeError(
            f"Discovery incomplete; listing pages failed after retries: {failed_pages}"
        )


async def process_record(record: dict, page, session: requests.Session, settings: dict, logger) -> None:
    document_id = record["document_id"]
    destination = settings["pdf_dir"] / f"{document_id}.pdf"
    record["local_pdf_path"] = str(destination)
    if valid_pdf(destination):
        record.update(status="downloaded", error="", updated_at=now_utc())
        return

    soup = await fetch_page(page, record["detail_url"])
    extract_metadata(soup, record, settings)
    observed = []

    for tag in soup.select("[href], [src]"):
        raw = tag.get("href") or tag.get("src")
        if raw:
            observed.append(urljoin(record["detail_url"], raw))
    candidates = candidates_from_html(soup, record["detail_url"], settings["base_url"])
    candidates.extend(url for url in observed if ".pdf" in url.lower())
    candidates = list(dict.fromkeys(candidates))
    record["pdf_url"] = candidates[0] if candidates else ""

    if not candidates:
        record.update(status="no_pdf", error="No PDF link found", updated_at=now_utc())
        return

    errors = []
    for url in candidates:
        for attempt in range(settings["max_retries"]):
            try:
                download_pdf(
                    session,
                    url,
                    destination,
                    record["detail_url"],
                    settings["request_timeout"],
                )
                record.update(status="downloaded", pdf_url=url, error="", updated_at=now_utc())
                return
            except Exception as error:
                errors.append(f"{url}: {error}")
                record["retry_count"] = str(int(record.get("retry_count") or 0) + 1)
                if attempt < settings["max_retries"] - 1:
                    await pause(settings)
    record.update(status="failed", error="; ".join(errors)[-2000:], updated_at=now_utc())


async def download_records(settings: dict, documents: dict[str, dict], logger) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": settings["user_agent"]})
    records_to_process = list(documents.values())
    if settings["test_mode"]:
        test_document_id = settings.get("test_document_id", "")
        if test_document_id:
            test_record = documents.get(test_document_id)
            if test_record is None:
                logger.warning(
                    "Test document %s was not discovered; increase TEST_PAGES or check the ID",
                    test_document_id,
                )
                return
            records_to_process = [test_record]
        else:
            records_to_process = records_to_process[: settings["test_max_documents"]]
        logger.info("Test mode: processing %s document(s)", len(records_to_process))
    async with async_playwright() as playwright:
        browser, page = await open_browser(playwright)
        try:
            for record in sorted(records_to_process, key=lambda item: item["document_id"]):
                document_id = record["document_id"]
                if record.get("status") == "downloaded" and valid_pdf(
                    settings["pdf_dir"] / f"{document_id}.pdf"
                ):
                    continue
                for attempt in range(settings["max_retries"]):
                    try:
                        await process_record(record, page, session, settings, logger)
                        break
                    except Exception as error:
                        record.update(
                            status="failed",
                            error=str(error)[-2000:],
                            retry_count=str(int(record.get("retry_count") or 0) + 1),
                            updated_at=now_utc(),
                        )
                        logger.warning(
                            "Document %s attempt %s failed: %s",
                            document_id,
                            attempt + 1,
                            error,
                        )
                        if "Target page, context or browser has been closed" in str(error):
                            logger.warning("Playwright browser closed; restarting it before retry")
                            try:
                                await browser.close()
                            except Exception:
                                pass
                            browser, page = await open_browser(playwright)
                        if attempt < settings["max_retries"] - 1:
                            await pause(settings)
                save_documents(settings["checkpoint_path"], documents)
                await pause(settings)
        finally:
            await browser.close()
    session.close()


def build_logger(path: Path) -> logging.Logger:
    logger = logging.getLogger("ncdd_scraper")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger


async def run(settings: dict) -> None:
    logger = build_logger(settings["log_path"])
    documents = load_documents(settings["checkpoint_path"])
    await discover_records(settings, documents, logger)
    await download_records(settings, documents, logger)
    counts = pd.Series([record.get("status", "unknown") for record in documents.values()]).value_counts()
    logger.info("Scraper finished: %s documents", len(documents))
    logger.info("Statuses: %s", counts.to_dict())


def run_pipeline(settings: dict) -> None:
    asyncio.run(run(settings))

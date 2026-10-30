from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import fitz


def valid_pdf(path: Path) -> bool:
    """Return True when a file has a valid, readable PDF with at least one page."""

    try:
        if path.stat().st_size <= 100 or path.read_bytes()[:5] != b"%PDF-":
            return False
        with fitz.open(path) as document:
            return document.page_count > 0
    except OSError:
        return False
    except Exception:
        return False


def candidates_from_html(soup, detail_url: str, base_url: str) -> list[str]:
    """Find likely PDF links in a detail page."""

    candidates = []
    for tag in soup.select("[href], [src], [data]"):
        for attribute in ("href", "src", "data"):
            raw = tag.get(attribute)
            if not raw or raw.startswith(("data:", "blob:", "javascript:")):
                continue
            url = urljoin(detail_url, raw)
            parsed = urlparse(url)
            label = tag.get_text(" ", strip=True).lower()
            is_pdf_host = parsed.hostname == "lib.ncdd.gov.kh"
            has_pdf_label = any(word in label for word in ("download", "ទាញយក", "pdf"))
            if parsed.scheme in ("http", "https") and (
                ".pdf" in parsed.path.lower() or is_pdf_host or has_pdf_label
            ):
                candidates.append(url)
    return list(dict.fromkeys(candidates))


def download_pdf(
    session: requests.Session,
    url: str,
    destination: Path,
    referer: str,
    timeout: tuple[int, int],
) -> None:
    """Download a PDF to a temporary path and replace the destination atomically."""

    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with session.get(
            url,
            headers={"Referer": referer},
            timeout=timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                raise ValueError("Received HTML instead of a PDF")
            with temporary.open("wb") as file:
                for chunk in response.iter_content(65536):
                    if chunk:
                        file.write(chunk)

        if not valid_pdf(temporary):
            raise ValueError("Invalid PDF signature or empty file")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)

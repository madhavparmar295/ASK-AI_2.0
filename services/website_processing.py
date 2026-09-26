import asyncio

from services.website_frontier import build_frontier
from services.website_fetch import fetch_page
from services.website_extract import extract_content
from services.website_pdf_dispatch import find_pdf_links, handle_website_pdf


def extract_from_website(domain: str) -> list[dict]:
    """
    Mirrors extract_from_email(message) -> list[dict].
    Returns one record per page (and, once wired, per linked PDF),
    ready for chunking/embedding in a LATER phase.
    """
    records = []
    for url in build_frontier(domain):
        record = _process_single_page(url)
        if record is not None:
            records.append(record)
    return records


def _process_single_page(url: str) -> dict | None:
    fetch_result = asyncio.run(fetch_page(url))
    extracted = extract_content(fetch_result["html"], url)
    if not extracted["text"].strip():
        return None  # nothing usable on this page

    record = _build_record(extracted["text"], url, extracted["title"])

    # PDF links found on this page -- stubbed for now (Step 4)
    for pdf_url in find_pdf_links(fetch_result["html"], url):
        print(f"[Found PDF link] {pdf_url} (extraction deferred)")

    return record


def _build_record(text: str, url: str, title: str) -> dict:
    """
    Deliberately NOT calling apply_pii_protection() or
    classify_access_level() here -- those come back once
    pii.py / access_control.py exist in the repo again.
    """
    return {
        "text": text,
        "source": title,
        "source_type": "website",
        "source_url": url,
        "doc_id": url,
    }

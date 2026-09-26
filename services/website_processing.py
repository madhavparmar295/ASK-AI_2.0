import asyncio
import sys

from services.website_frontier import build_frontier
from services.website_fetch import fetch_page
from services.website_extract import extract_content, find_pdf_links


def extract_from_website(domain):
    print(f"[Website] Starting ingestion: {domain}")

    urls = build_frontier(domain)
    print(f"[Website] Discovered {len(urls)} URLs")

    records = []

    for index, url in enumerate(urls, start=1):
        print(f"\n[Website] Processing {index}/{len(urls)}")
        print(f"[Website] URL: {url}")

        try:
            record = _process_single_page(url)

            if record:
                records.append(record)

        except Exception as e:
            print(f"[Website] Failed processing: {url}")
            print(f"[Website] Error: {type(e).__name__}: {e}")

    return records


def _process_single_page(url):
    fetch_result = asyncio.run(fetch_page(url))

    # Fetch failed — skip this page instead of crashing the crawl.
    if not fetch_result:
        print(f"[Website] Skipping page because fetch failed: {url}")
        return None

    html = fetch_result.get("html")

    if not html:
        print(f"[Website] Skipping page because HTML is empty: {url}")
        return None

    extracted = extract_content(html, url)

    if not extracted:
        print(f"[Website] No extractable content: {url}")
        return None

    text = extracted.get("text", "").strip()
    title = extracted.get("title", url)

    if not text:
        print(f"[Website] Empty extracted text: {url}")
        return None

    pdf_links = find_pdf_links(html, url)

    if pdf_links:
        for pdf_url in pdf_links:
            print(f"[Website] PDF found (deferred): {pdf_url}")

    return _build_record(
        url=url,
        title=title,
        text=text,
    )


def _build_record(url, title, text):
    return {
        "text": text,
        "source": title,
        "source_type": "website",
        "source_url": url,
        "doc_id": url,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python -m services.website_processing <website_url>\n\n"
            "Example:\n"
            "  python -m services.website_processing https://iitj.ac.in"
        )
        sys.exit(1)

    domain = sys.argv[1]

    records = extract_from_website(domain)

    print("\n" + "=" * 80)
    print("[Website] Extraction completed")
    print(f"[Website] Total extracted pages: {len(records)}")
    print("=" * 80)

    for index, record in enumerate(records, start=1):
        print("\n" + "-" * 80)
        print(f"PAGE {index}")
        print(f"URL: {record['source_url']}")
        print(f"Title: {record['source']}")
        print("-" * 80)
        print(record["text"][:2000])

        if len(record["text"]) > 2000:
            print("\n...[text truncated for terminal display]...")

    print("\n" + "=" * 80)
    print("No data was stored.")
    print("No Celery or Redis was used.")
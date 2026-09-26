import trafilatura
import pandas as pd
from io import StringIO

LOW_CONTENT_THRESHOLD_CHARS = 100


def extract_content(html: str, url: str) -> dict:
    """Returns {"text": ..., "low_content": bool, "title": ...}"""
    main_text = trafilatura.extract(html, favor_recall=True) or ""
    tables_md = ""
    try:
        tables = pd.read_html(StringIO(html))
        for df in tables:
            tables_md += df.to_markdown(index=False) + "\n\n"
    except ValueError:
        pass  # no <table> elements on this page -- fine, not an error

    full_text = (main_text + "\n\n" + tables_md).strip()
    return {
        "text": full_text,
        "low_content": len(full_text) < LOW_CONTENT_THRESHOLD_CHARS,
        "title": extract_title(html) or url,
    }


def extract_title(html: str) -> str:
    metadata = trafilatura.extract_metadata(html)
    return metadata.title if metadata and metadata.title else ""


# low_content=True is a flag, not a rejection -- near-empty pages are kept and
# marked for review rather than silently dropped, matching the same instinct as
# email_processing.py returning None only for genuinely empty attachments.

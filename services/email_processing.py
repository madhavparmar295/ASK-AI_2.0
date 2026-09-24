"""
Single shared entry point for extracting structured, protected, tagged
content from a raw Gmail message.

Used by both historical backfill and real-time ingestion.

Pipeline per email:

    sender check
    -> dedup check
    -> body + each attachment dispatched to the right extractor
    -> OCR-cache check/write for attachments that actually needed OCR
    -> PII hashing (roll numbers, grades)
    -> access-level classification
    -> return one record per body/attachment
"""

import base64
import hashlib
import os
import tempfile
from html.parser import HTMLParser

from services.attachment_processor import (
    process_attachment,
    attachment_required_ocr,
)
from services.pii import apply_pii_protection
from services.access_control import classify_access_level
from services.ocr_cache import (
    get_cached_ocr_result,
    store_ocr_result,
)
from services.dedup import (
    is_already_processed,
    mark_processed,
)
from services.sender_filter import is_allowed_sender


class _HTMLTextExtractor(HTMLParser):
    """Small standard-library HTML -> text converter."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def _extract_headers(message: dict) -> dict:
    headers = message.get("payload", {}).get("headers", [])

    header_map = {
        h.get("name", "").lower(): h.get("value", "")
        for h in headers
        if isinstance(h, dict)
    }

    return {
        "sender": header_map.get("from", ""),
        "subject": header_map.get("subject", "No Subject"),
        "date": header_map.get("date", ""),
    }


def extract_from_email(
    message: dict,
    gmail=None,
) -> list[dict]:
    """
    Extract structured records from one Gmail message.

    Returns one record per email body/attachment, ready for
    chunking and embedding.
    """

    message_id = message["id"]

    # Second sender-protection layer.
    # email_tasks.py already performs an early metadata check,
    # but extraction must protect itself as well.
    email_meta = _extract_headers(message)

    if not is_allowed_sender(email_meta.get("sender", "")):
        print(
            f"[Sender Filter] Rejected message {message_id}: "
            f"{email_meta.get('sender', '')}"
        )
        return []

    if is_already_processed(message_id):
        return []

    records = []

    body_text = _extract_body(message)

    if body_text.strip():
        records.append(
            _build_record(
                body_text,
                source="body",
                doc_id=message_id,
                meta=email_meta,
            )
        )

    for attachment in _get_attachments(
        message,
        gmail=gmail,
    ):
        record = _process_single_attachment(
            attachment,
            message_id,
            meta=email_meta,
        )

        if record is not None:
            records.append(record)

    mark_processed(message_id)

    return records


def _build_record(
    raw_text: str,
    source: str,
    doc_id: str,
    meta: dict = None,
    filename: str = "",
) -> dict:
    protected_text = apply_pii_protection(raw_text)

    access_level = classify_access_level(protected_text)

    record = {
        "text": protected_text,
        "source": source,
        "source_type": "email",
        "access_level": access_level,
        "doc_id": doc_id,
    }

    if meta:
        sender = meta.get("sender", "")
        subject = meta.get("subject", "")
        date = meta.get("date", "")

        header_prefix = (
            f"[Sender: {sender} | "
            f"Subject: {subject} | "
            f"Date: {date}]\n"
        )

        record["text"] = (
            header_prefix + protected_text
        )

        record["sender"] = sender
        record["subject"] = subject
        record["date"] = date
        record["filename"] = (
            filename if filename else source
        )

    return record


def _process_single_attachment(
    attachment: dict,
    message_id: str,
    meta: dict = None,
) -> dict | None:
    filename = attachment["filename"]

    ext = (
        filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    raw_bytes = attachment.get("bytes") or (
        base64.urlsafe_b64decode(
            attachment["data"]
        )
        if attachment.get("data")
        else b""
    )

    if not raw_bytes:
        return None

    content_hash = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    # Hash-based OCR cache.
    cached_text = get_cached_ocr_result(
        content_hash
    )

    if cached_text is not None:
        return _build_record(
            cached_text,
            source=filename,
            doc_id=f"{message_id}:{filename}",
            meta=meta,
            filename=filename,
        )

    with tempfile.NamedTemporaryFile(
        suffix=f".{ext}",
        delete=False,
    ) as tmp:
        tmp.write(raw_bytes)
        temp_path = tmp.name

    try:
        text = process_attachment(
            temp_path,
            ext,
        )

        if not text.strip():
            return None

        # Check whether OCR was required before
        # removing the temporary file.
        if attachment_required_ocr(
            temp_path,
            ext,
        ):
            store_ocr_result(
                content_hash,
                text,
            )

    except ValueError:
        # Unsupported attachment type.
        return None

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return _build_record(
        text,
        source=filename,
        doc_id=f"{message_id}:{filename}",
        meta=meta,
        filename=filename,
    )


def _extract_body(message: dict) -> str:
    """
    Pull text from Gmail's nested MIME payload.

    Prefer text/plain. If no usable plain-text body exists,
    fall back to text/html.
    """
    payload = message.get("payload", {})

    plain_text = _extract_mime_part(
        payload,
        "text/plain",
    )

    if plain_text.strip():
        return plain_text

    html_text = _extract_mime_part(
        payload,
        "text/html",
    )

    if html_text.strip():
        return _html_to_text(html_text)

    return ""


def _extract_mime_part(
    payload: dict,
    mime_type: str,
) -> str:
    """
    Recursively find and decode the first requested MIME part.
    """
    if payload.get("mimeType") == mime_type:
        data = payload.get("body", {}).get(
            "data",
            "",
        )

        if data:
            try:
                return base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="ignore",
                )
            except Exception:
                return ""

    for part in payload.get("parts", []):
        result = _extract_mime_part(
            part,
            mime_type,
        )

        if result:
            return result

    return ""


def _html_to_text(html: str) -> str:
    """
    Convert HTML body content into plain text.
    """
    parser = _HTMLTextExtractor()
    parser.feed(html)
    parser.close()

    return " ".join(
        parser.get_text().split()
    )


def _get_attachments(
    message: dict,
    gmail=None,
) -> list[dict]:
    """
    Returns:
        [{filename, data, bytes}]
    for every attachment part in the message.
    """
    attachments = []

    message_id = message.get("id")
    payload = message.get("payload", {})

    def _walk_parts(parts):
        for part in parts:
            filename = part.get("filename")
            body = part.get("body", {})
            attachment_id = body.get(
                "attachmentId"
            )

            if filename and attachment_id:
                raw_bytes = b""

                data = body.get("data")

                if data:
                    raw_bytes = (
                        base64.urlsafe_b64decode(data)
                    )

                elif gmail and message_id:
                    try:
                        att_res = (
                            gmail.users()
                            .messages()
                            .attachments()
                            .get(
                                userId="me",
                                messageId=message_id,
                                id=attachment_id,
                            )
                            .execute()
                        )

                        att_data = att_res.get(
                            "data",
                            "",
                        )

                        if att_data:
                            raw_bytes = (
                                base64.urlsafe_b64decode(
                                    att_data
                                )
                            )

                    except Exception as exc:
                        print(
                            f"Failed to fetch attachment "
                            f"{attachment_id} for msg "
                            f"{message_id}: {exc}"
                        )

                attachments.append(
                    {
                        "filename": filename,
                        "data": data or "",
                        "bytes": raw_bytes,
                        "attachmentId": attachment_id,
                    }
                )

            if "parts" in part:
                _walk_parts(part["parts"])

    _walk_parts(
        payload.get("parts", [payload])
    )

    return attachments
from googleapiclient.discovery import build

from jobs.celery_app import celery_app

from services.gmail_auth import get_valid_credentials
#from services.email_processing import extract_from_email
#from services.chunking import chunk_record
#from services.embeddings import embed_chunks
#from services.vectorstore import upsert_chunks
from services.rate_limiter import acquire_token
from services.sender_filter import (
    fetch_from_header,
    is_allowed_sender,
)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
)
def process_new_email_task(
    self,
    user_id: str,
    message_id: str,
):
    try:
        acquire_token(bucket="gmail_api")

        creds = get_valid_credentials(user_id)

        gmail = build(
            "gmail",
            "v1",
            credentials=creds,
        )

        # Check the sender using metadata BEFORE downloading
        # the full email body.
        from_header = fetch_from_header(
            gmail,
            message_id,
        )

        if not is_allowed_sender(from_header):
            print(
                f"[Sender Filter] Rejected message "
                f"{message_id}: {from_header}"
            )
            return

        # Only allowed IITJ messages reach the full-message fetch.
        message = (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

        _index_email(
            message,
            gmail=gmail,
        )

    except Exception as exc:
        # Actual processing/API failures are retried.
        # Sender rejection above is returned normally and is NOT retried.
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_backfill_batch_task(
    self,
    user_id: str,
    message_ids: list[str],
):
    creds = get_valid_credentials(user_id)

    gmail = build(
        "gmail",
        "v1",
        credentials=creds,
    )

    for message_id in message_ids:
        try:
            acquire_token(bucket="gmail_api")

            # Check sender metadata BEFORE fetching the full message.
            from_header = fetch_from_header(
                gmail,
                message_id,
            )

            if not is_allowed_sender(from_header):
                print(
                    f"[Sender Filter] Rejected backfill message "
                    f"{message_id}: {from_header}"
                )
                continue

            message = (
                gmail.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="full",
                )
                .execute()
            )

            _index_email(
                message,
                gmail=gmail,
            )

        except Exception as exc:
            # A failure on one message should not kill the batch.
            print(
                f"Failed to process message {message_id}: {exc}"
            )
            continue


def _index_email(
    message: dict,
    gmail=None,
) -> None:
    """
    Shared tail end:
    extract -> chunk -> embed -> upsert.
    """
    records = extract_from_email(
        message,
        gmail=gmail,
    )

    if not records:
        print(
            f"[Dedup] Email {message.get('id')} "
            "already processed or empty. Skipping."
        )
        return

    for record in records:
        chunks = chunk_record(record)

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = embed_chunks(texts)

        upsert_chunks(
            chunks,
            embeddings,
        )

        print(
            f"[Pinecone] Successfully stored "
            f"{len(chunks)} chunk(s) for source "
            f"'{record.get('source')}' "
            f"(doc_id: {record.get('doc_id')})."
        )
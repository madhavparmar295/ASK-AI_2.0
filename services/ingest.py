from services.doc_embeddings import embed_document
from services.postgres import upsert_document


def ingest_record(record: dict) -> None:
    """Store document metadata + 384-d embedding in PostgreSQL.

    Two text fields are recognised:
    - "text"       : stored as the `content` column in postgres.
                     For email bodies this is the full extracted text.
                     For attachments / manual uploads this is intentionally
                     left empty — the raw file lives on disk at attachment_path.
    - "embed_text" : used ONLY for computing the 384-d HNSW embedding.
                     Callers that set text="" still pass the real extracted text
                     here so the document-level vector stays semantically useful.
                     Falls back to "text" when absent (email body case).

    Chunks are not sent to Pinecone here. They are created from the top-2
    documents at query time and upserted then.
    """
    embed_text = record.get("embed_text") or record.get("text") or ""
    embedding = embed_document(embed_text)
    upsert_document(record, embedding)

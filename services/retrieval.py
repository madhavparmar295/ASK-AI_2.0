from services.access_control import allowed_access_levels
from services.chunking import chunk_record
from services.doc_embeddings import embed_query_384
from services.embeddings import embed_chunks, embed_query
from services.postgres import (
    get_attachments_for_message,
    get_document_by_id,
    mark_pinecone_indexed,
    row_to_record,
    search_documents,
)
from services.vectorstore import query_similar, upsert_chunks
from services.document_loader import load_document
from services.pii import apply_pii_protection

TOP_DOCUMENTS = 4
TOP_CHUNKS = 5


def _index_document_chunks(doc: dict) -> None:
    # Convert DB row to full record dict (includes attachment_path if present)
    record = row_to_record(doc)

    # If the record has an attachment on disk, load the original file from storage
    if record.get("attachment_path"):
        try:
            loaded_text = load_document(record["attachment_path"])
            if loaded_text and loaded_text.strip():
                protected_text = apply_pii_protection(loaded_text)
                header_prefix = ""
                sender = record.get("sender")
                subject = record.get("subject")
                date = record.get("date")
                filename = record.get("filename")
                source_type = record.get("source_type")
                if sender or subject or date:
                    header_prefix = f"[From: {sender or 'Unknown'} | Subject: {subject or 'No Subject'} | Date: {date or 'N/A'} | Attachment: {filename or 'File'}]\n"
                elif source_type == "website_pdf":
                    header_prefix = f"[Source: {record.get('source') or filename} | File: {filename or 'File'}]\n"
                elif filename:
                    header_prefix = f"[File: {filename}]\n"
                record["text"] = header_prefix + protected_text
        except Exception as e:
            print(f"[Retrieval] Failed to load attachment from {record.get('attachment_path')}: {e}")
            if not record.get("text"):
                record["text"] = ""
    elif not record.get("text"):
        record["text"] = ""

    chunks = chunk_record(record)
    # Ensure chunks have non-empty text before passing to embedding/Pinecone
    chunks = [c for c in chunks if c.get("text", "").strip()]
    if not chunks:
        mark_pinecone_indexed(doc["doc_id"])
        return

    texts = [c["text"] for c in chunks]
    embeddings = embed_chunks(texts)
    if not embeddings:
        mark_pinecone_indexed(doc["doc_id"])
        return

    upsert_chunks(chunks, embeddings)
    mark_pinecone_indexed(doc["doc_id"])


def expand_linked_documents(documents: list[dict]) -> list[dict]:
    """Ensure both the email attachment (doc) and the email body are available in documents."""
    doc_dict = {doc["doc_id"]: doc for doc in documents}

    for doc in list(documents):
        doc_id = doc.get("doc_id", "")
        source_type = doc.get("source_type", "")

        # If it's an email attachment (message_id:filename), fetch the parent email body
        if ":" in doc_id or source_type == "email_attachment":
            parent_id = doc_id.split(":", 1)[0]
            if parent_id not in doc_dict:
                parent_doc = get_document_by_id(parent_id)
                if parent_doc:
                    doc_dict[parent_id] = parent_doc

        # If it's an email body, fetch any attachments belonging to this email
        elif source_type == "email":
            attachments = get_attachments_for_message(doc_id)
            for att in attachments:
                if att["doc_id"] not in doc_dict:
                    doc_dict[att["doc_id"]] = att

    return list(doc_dict.values())


def enrich_matches_with_linked_bodies(matches: list[dict], documents: list[dict]) -> list[dict]:
    """
    If an attachment (doc) was matched, guarantee the parent email body is returned.
    If an email body was matched, guarantee the associated document is returned.
    """
    if not matches:
        return []

    doc_map = {doc["doc_id"]: doc for doc in documents}
    matched_doc_ids = {
        m["metadata"]["doc_id"]
        for m in matches
        if isinstance(m.get("metadata"), dict) and "doc_id" in m["metadata"]
    }

    enriched = list(matches)
    for m in list(matches):
        doc_id = m.get("metadata", {}).get("doc_id", "")
        source_type = m.get("metadata", {}).get("source_type", "")

        # 1. Attachment matched -> append email body chunk
        if ":" in doc_id or source_type == "email_attachment":
            parent_id = doc_id.split(":", 1)[0]
            if parent_id not in matched_doc_ids and parent_id in doc_map:
                parent_doc = doc_map[parent_id]
                parent_content = parent_doc.get("content") or ""
                if parent_content.strip():
                    body_chunk = {
                        "id": f"{parent_id}-linked-body",
                        "score": m["score"] * 0.95,
                        "metadata": {
                            "text": parent_content[:1000],
                            "doc_id": parent_id,
                            "access_level": parent_doc.get("access_level", "public"),
                            "sender": parent_doc.get("sender", ""),
                            "subject": parent_doc.get("subject", ""),
                            "date": parent_doc.get("date", ""),
                            "source": parent_doc.get("source", "body"),
                            "source_type": parent_doc.get("source_type", "email"),
                            "filename": parent_doc.get("filename", "body"),
                        },
                    }
                    enriched.append(body_chunk)
                    matched_doc_ids.add(parent_id)

        # 2. Email body matched -> append attachment doc chunk
        elif source_type == "email":
            for doc in documents:
                att_id = doc.get("doc_id", "")
                if (att_id.startswith(f"{doc_id}:") or doc.get("source_type") == "email_attachment") and att_id not in matched_doc_ids:
                    att_path = doc.get("attachment_path")
                    att_text = ""
                    if att_path:
                        try:
                            att_text = load_document(att_path)
                        except Exception:
                            att_text = ""
                    if not att_text:
                        att_text = doc.get("content") or ""

                    if att_text.strip():
                        att_chunk = {
                            "id": f"{att_id}-linked-doc",
                            "score": m["score"] * 0.95,
                            "metadata": {
                                "text": att_text[:1000],
                                "doc_id": att_id,
                                "access_level": doc.get("access_level", "public"),
                                "sender": doc.get("sender", ""),
                                "subject": doc.get("subject", ""),
                                "date": doc.get("date", ""),
                                "source": doc.get("source", doc.get("filename", "")),
                                "source_type": doc.get("source_type", "email_attachment"),
                                "filename": doc.get("filename", ""),
                            },
                        }
                        enriched.append(att_chunk)
                        matched_doc_ids.add(att_id)

    return enriched


def retrieve_chunks(question: str, user_tag: str | None = None) -> list[dict]:
    """Two-stage search: Postgres HNSW (top docs) then Pinecone (top chunks)."""
    allowed = None
    if user_tag:
        allowed = allowed_access_levels(user_tag)
        if "general" not in allowed:
            allowed.append("general")

    query_384 = embed_query_384(question)
    documents = search_documents(query_384, allowed_levels=allowed, top_k=TOP_DOCUMENTS)
    if not documents:
        return []

    # Expand to include linked doc + email body
    documents = expand_linked_documents(documents)

    for doc in documents:
        if not doc.get("pinecone_indexed"):
            _index_document_chunks(doc)

    query_1024 = embed_query(question)
    doc_ids = [doc["doc_id"] for doc in documents]
    results = query_similar(
        query_1024,
        user_tag=user_tag,
        top_k=TOP_CHUNKS,
        doc_ids=doc_ids,
    )
    matches = results.get("matches", [])

    # Ensure doc + email body are both returned
    matches = enrich_matches_with_linked_bodies(matches, documents)

    return matches

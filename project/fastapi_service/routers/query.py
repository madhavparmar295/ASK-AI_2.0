from typing import Optional
from fastapi import APIRouter, Depends
from schemas.query import QueryRequest, QueryResponse, SourceChunk
from services.access_control import resolve_user_tag
from services.embeddings import embed_query
from services.rag import generate_answer, rewrite_query
from services.security import get_optional_current_user
from services.vectorstore import query_similar
from models.user import User

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    # Determine user identity and role:
    # 1. If user is logged in with a verified token, use the authenticated email
    # 2. If not logged in, user is strictly treated as 'Guest' and cannot access restricted data
    if current_user and current_user.is_verified:
        active_email = current_user.email
        domain = active_email.split("@")[-1].lower()
        user_tag = resolve_user_tag(domain)
    else:
        # Unauthenticated / Guest: strictly public data access
        active_email = "guest@ask-ai.local"
        user_tag = "Guest"

    # Coreference resolution: rewrite follow-up questions (e.g. "what has he done")
    # into self-contained search queries (e.g. "What has Prof. Avinash Kumar Agarwal done?")
    search_query = rewrite_query(request.question, chat_history=request.chat_history)

    query_embedding = embed_query(search_query)
    results = query_similar(query_embedding, user_tag=user_tag, top_k=10)

    matches = results["matches"]
    context_chunks = [
        {
            "text": match["metadata"]["text"],
            "score": match["score"],
            "doc_id": match["metadata"]["doc_id"],
            "access_level": match["metadata"]["access_level"],
            "sender": match["metadata"].get("sender", ""),
            "subject": match["metadata"].get("subject", ""),
            "date": match["metadata"].get("date", ""),
            "source_type": match["metadata"].get("source_type", "unknown"),
        }
        for match in matches
    ]

    answer = generate_answer(request.question, context_chunks, chat_history=request.chat_history)

    sources = [
        SourceChunk(
            text=match["metadata"]["text"],
            score=match["score"],
            doc_id=match["metadata"]["doc_id"],
            access_level=match["metadata"]["access_level"],
            sender=match["metadata"].get("sender"),
            subject=match["metadata"].get("subject"),
            date=match["metadata"].get("date"),
            source=match["metadata"].get("source"),
            source_type=match["metadata"].get("source_type"),
        )
        for match in matches
    ]

    return QueryResponse(question=request.question, answer=answer, sources=sources)

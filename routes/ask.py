import re
from fastapi import APIRouter, Depends, Request
from app import config
from app.schemas import AskRequest
from app.services.retrieval import retrieve_chunks, is_summary_query, get_document_summary
from app.services.llm import generate_answer, generate_document_summary
from app.services.rate_limit import limiter
from app.database import get_db
from app.deps import get_session_id, get_client_ip
from app.models import Document, Chunk


router = APIRouter()

NO_DOCUMENTS_MESSAGE = (
    "Upload a PDF first. I can only answer questions about documents you upload "
    "in this session (Hãy tải lên một tệp PDF trước)."
)


@router.post("/ask")
async def ask(
    request: AskRequest,
    http_request: Request,
    db=Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    limiter.check(f"ask-session:{session_id}", config.ASK_PER_MINUTE_SESSION, 60, "questions")
    limiter.check(f"ask-ip:{get_client_ip(http_request)}", config.ASK_PER_HOUR_IP, 3600, "questions")

    # 1. Only this session's documents exist as far as this request is concerned.
    session_docs = (
        db.query(Document)
        .filter(Document.session_id == session_id)
        .order_by(Document.id.desc())
        .all()
    )
    if not session_docs:
        # No retrieval, no model call.
        return {"answer": NO_DOCUMENTS_MESSAGE, "is_summary": False, "needs_upload": True}

    owned = {d.id: d for d in session_docs}
    q_lower = request.question.lower()

    # 2. Narrow to the documents the client asked for; ids that aren't ours are ignored.
    requested = []
    if request.document_id:
        requested.append(request.document_id)
    requested.extend(request.document_ids or [])
    target_ids = [i for i in dict.fromkeys(requested) if i in owned]

    names = list(request.document_names or [])
    if request.filename:
        names.append(request.filename)
    for name in names:
        for d in session_docs:
            if name.lower() in d.filename.lower() and d.id not in target_ids:
                target_ids.append(d.id)

    # 3. Smart document resolution by hints in the question (within this session only)
    doc_hints = {
        r"\b(cv|resume|hồ sơ|ly lich)\b": ["cv", "resume"],
        r"\b(hợp đồng|thue nha|agreement|lease|rent)\b": ["agreement", "shared house", "contract"],
        r"\b(học bổng|scholarship)\b": ["scholarship", "vcis"],
        r"\b(assignment|bai tap)\b": ["assignment", "math"],
        r"\b(cheatsheet)\b": ["cheatsheet"],
    }
    for pattern, keywords in doc_hints.items():
        if re.search(pattern, q_lower):
            for kw in keywords:
                for d in session_docs:
                    if kw in d.filename.lower() and d.id not in target_ids:
                        target_ids.insert(0, d.id)
            break

    if not target_ids:
        target_ids = [d.id for d in session_docs]

    # 4. Summary query handling
    if is_summary_query(request.question):
        primary_doc_id = target_ids[0]
        summary = get_document_summary(db, session_id, primary_doc_id)
        if summary and not summary.startswith("Summary generation failed") and len(summary.strip()) > 30:
            return {"answer": summary, "is_summary": True}

        all_chunks = [
            c.content
            for c in db.query(Chunk)
            .filter(Chunk.document_id == primary_doc_id, Chunk.session_id == session_id)
            .all()
        ]
        if all_chunks:
            try:
                summary = generate_document_summary("\n\n".join(all_chunks))
                owned[primary_doc_id].summary = summary
                db.commit()
                return {"answer": summary, "is_summary": True}
            except Exception as e:
                print(f"Error generating summary: {e}")

    # 5. Point queries: search only the target documents of this session.
    chunks = retrieve_chunks(request.question, db, session_id, top_k=12, document_ids=target_ids)
    if not chunks:
        return {"answer": NO_DOCUMENTS_MESSAGE, "is_summary": False, "needs_upload": True}

    answer = generate_answer(request.question, chunks)
    return {"answer": answer, "is_summary": False}

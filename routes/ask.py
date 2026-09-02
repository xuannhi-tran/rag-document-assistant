from fastapi import APIRouter, Depends
import re
from app.schemas import AskRequest
from app.services.retrieval import retrieve_chunks, is_summary_query, get_latest_document_summary
from app.services.llm import generate_answer, generate_document_summary
from app.database import get_db
from app.models import Document, Chunk


router = APIRouter()

@router.post("/ask")
async def ask(request: AskRequest, db=Depends(get_db)):
    doc_id = request.document_id
    q_lower = request.question.lower()

    # 1. Resolve document scope from client (active documents in sidebar)
    target_ids = []
    if request.document_id:
        target_ids.append(request.document_id)
    if request.document_ids:
        target_ids.extend([i for i in request.document_ids if i not in target_ids])
    if request.document_names:
        for name in request.document_names:
            matching = db.query(Document).filter(Document.filename.ilike(f"%{name}%")).all()
            for m in matching:
                if m.id not in target_ids:
                    target_ids.append(m.id)
    elif request.filename:
        matching = db.query(Document).filter(Document.filename.ilike(f"%{request.filename}%")).all()
        for m in matching:
            if m.id not in target_ids:
                target_ids.append(m.id)

    # 2. Smart document resolution if question explicitly mentions document types (e.g., 'cv', 'resume', 'hợp đồng', 'scholarship')
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
                found_docs = db.query(Document).filter(Document.filename.ilike(f"%{kw}%")).order_by(Document.id.desc()).all()
                for f in found_docs:
                    if f.id not in target_ids:
                        target_ids.insert(0, f.id)
            break

    # 3. Summary query handling
    if is_summary_query(request.question):
        primary_doc_id = target_ids[0] if target_ids else None
        if not primary_doc_id:
            latest = db.query(Document).order_by(Document.id.desc()).first()
            primary_doc_id = latest.id if latest else None

        if primary_doc_id:
            summary = get_latest_document_summary(db, document_id=primary_doc_id)
            if summary and not summary.startswith("Summary generation failed") and len(summary.strip()) > 30:
                return {"answer": summary, "is_summary": True}

            all_chunks = [c.content for c in db.query(Chunk).filter(Chunk.document_id == primary_doc_id).all()]
            if all_chunks:
                full_text = "\n\n".join(all_chunks)
                try:
                    summary = generate_document_summary(full_text)
                    doc = db.query(Document).filter(Document.id == primary_doc_id).first()
                    if doc:
                        doc.summary = summary
                        db.commit()
                    return {"answer": summary, "is_summary": True}
                except Exception as e:
                    print(f"Error generating summary: {e}")

    # 4. Point Queries: Search across target documents (or all if none specified)
    chunks = retrieve_chunks(request.question, db, top_k=12, document_ids=target_ids if target_ids else None)
    
    if not chunks and target_ids:
        # Fallback to search entire database if targeted filter returned 0
        chunks = retrieve_chunks(request.question, db, top_k=12)


    answer = generate_answer(request.question, chunks)
    return {"answer": answer, "is_summary": False}





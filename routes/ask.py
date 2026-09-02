from fastapi import APIRouter, Depends
from app.schemas import AskRequest
from app.services.retrieval import retrieve_chunks, is_summary_query, get_latest_document_summary
from app.services.llm import generate_answer, generate_document_summary
from app.database import get_db
from app.models import Document, Chunk


router = APIRouter()

@router.post("/ask")
async def ask(request: AskRequest, db=Depends(get_db)):
    doc_id = request.document_id

    # If filename is specified but doc_id is not, find the matching document
    if not doc_id and request.filename:
        matching_doc = db.query(Document).filter(Document.filename == request.filename).order_by(Document.id.desc()).first()
        if matching_doc:
            doc_id = matching_doc.id

    # If no doc_id found, default to the most recent document
    if not doc_id:
        latest_doc = db.query(Document).order_by(Document.id.desc()).first()
        if latest_doc:
            doc_id = latest_doc.id

    # 1. Check if this is a general document summary / overview question
    if is_summary_query(request.question):
        # Check for precomputed summary in database
        summary = get_latest_document_summary(db, document_id=doc_id)
        if summary and not summary.startswith("Summary generation failed") and len(summary.strip()) > 30:
            return {"answer": summary, "is_summary": True}

        # On-the-fly fallback: Pull all chunks for the active document and summarize now
        chunks_query = db.query(Chunk)
        if doc_id:
            chunks_query = chunks_query.filter(Chunk.document_id == doc_id)
        
        all_chunks = [c.content for c in chunks_query.all()]
        if all_chunks:
            full_text = "\n\n".join(all_chunks)
            try:
                summary = generate_document_summary(full_text)
                # Cache it back to the Document record
                if doc_id:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    if doc:
                        doc.summary = summary
                        db.commit()
                return {"answer": summary, "is_summary": True}
            except Exception as e:
                print(f"Error generating on-the-fly summary: {e}")

    # 2. Specific question: Perform vector search across document chunks
    chunks = retrieve_chunks(request.question, db, top_k=6, document_id=doc_id)
    
    if not chunks:
        # Fallback across all chunks if specific document filtering returned 0
        chunks = retrieve_chunks(request.question, db, top_k=6)

    answer = generate_answer(request.question, chunks)
    return {"answer": answer, "is_summary": False}



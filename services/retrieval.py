import re
from app.models import Chunk, Document
from app.services.embedding import generate_embedding


def is_summary_query(question: str) -> bool:
    """
    Determines if the user query is asking for a general document summary or overview.
    """
    q = question.lower().strip()
    summary_keywords = [
        r"\bsummarize\b",
        r"\bsummary\b",
        r"\boverview\b",
        r"\btldr\b",
        r"\btl;dr\b",
        r"what is this (document|pdf|paper|file) about",
        r"what is the (document|pdf|paper|file) about",
        r"key (takeaways|findings|points)",
        r"main (points|ideas|topics|conclusions)",
        r"brief(ly)? (explain|describe) the (document|pdf|paper|file)",
    ]
    return any(re.search(pattern, q) for pattern in summary_keywords)


def get_latest_document_summary(db_session, document_id=None) -> str | None:
    """
    Retrieves the precomputed summary of the specified or most recently uploaded document.
    """
    if document_id:
        doc = db_session.query(Document).filter(Document.id == document_id).first()
    else:
        doc = db_session.query(Document).order_by(Document.id.desc()).first()

    if doc and doc.summary:
        return doc.summary
    return None


def retrieve_chunks(question, db_session, top_k=5, document_id=None):
    # Generate embedding for the question
    question_embedding = generate_embedding(question)
    
    query = db_session.query(Chunk)
    if document_id:
        query = query.filter(Chunk.document_id == document_id)
        
    chunks = (
        query
        .order_by(Chunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )
    
    # Return the text content of the retrieved chunks
    return [chunk.content for chunk in chunks]
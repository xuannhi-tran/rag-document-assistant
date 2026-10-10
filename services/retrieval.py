import re
from app.models import Chunk, Document
from app.services.embedding import generate_embedding


def is_summary_query(question: str) -> bool:
    """
    Determines if the user query is asking for a general document summary or overview
    in either English or Vietnamese.
    """
    q = question.lower().strip()
    summary_keywords = [
        # English patterns
        r"\bsummarize\b",
        r"\bsummary\b",
        r"\boverview\b",
        r"\btldr\b",
        r"\btl;dr\b",
        r"what is this (document|pdf|paper|file|resume|cv) about",
        r"what is the (document|pdf|paper|file|resume|cv) about",
        r"key (takeaways|findings|points)",
        r"main (points|ideas|topics|conclusions)",
        r"brief(ly)? (explain|describe) the (document|pdf|paper|file)",
        
        # Vietnamese patterns (with and without diacritics)
        r"tóm tắt",
        r"tom tat",
        r"tổng quan",
        r"tong quan",
        r"tổng kết",
        r"tong ket",
        r"khái quát",
        r"khai quat",
        r"nội dung chính",
        r"noi dung chinh",
        r"ý chính",
        r"y chinh",
        r"điểm chính",
        r"diem chinh",
        r"(tài liệu|file|bài viết|cv|hồ sơ|văn bản) này nói về (gì|cái gì)",
        r"(tài liệu|file|bài viết|cv|hồ sơ|văn bản) nói về (gì|cái gì)",
    ]
    return any(re.search(pattern, q) for pattern in summary_keywords)



def get_document_summary(db_session, session_id: str, document_id: int) -> str | None:
    """Precomputed summary of a document, only if it belongs to the session."""
    doc = (
        db_session.query(Document)
        .filter(Document.id == document_id, Document.session_id == session_id)
        .first()
    )
    return doc.summary if doc and doc.summary else None


def retrieve_chunks(question, db_session, session_id: str, top_k=8, document_ids=None):
    """Vector search restricted to one session's chunks. session_id is mandatory
    and always applied; document_ids can only narrow the result further."""
    if not session_id:
        raise ValueError("session_id is required")
    question_embedding = generate_embedding(question)

    query = (
        db_session.query(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Chunk.session_id == session_id, Document.session_id == session_id)
    )
    if document_ids:
        query = query.filter(Chunk.document_id.in_(document_ids))

    results = (
        query
        .order_by(Chunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )

    # Return context chunks with source document attribution
    return [f"[Nguồn / Source Document: {filename}]\n{chunk.content}" for chunk, filename in results]

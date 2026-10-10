from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.deps import get_session_id
from app.models import Document
from app.services.cleanup import delete_documents

router = APIRouter()


@router.get("/documents")
async def list_documents(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    docs = (
        db.query(Document)
        .filter(Document.session_id == session_id)
        .order_by(Document.id.desc())
        .all()
    )
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "size_bytes": d.size_bytes,
                "uploaded_at": d.upload_date.isoformat() if d.upload_date else None,
            }
            for d in docs
        ],
        "limits": {
            "max_files": config.MAX_FILES_PER_SESSION,
            "max_file_mb": config.MAX_FILE_MB,
            "retention_hours": config.RETENTION_HOURS,
        },
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int, db: Session = Depends(get_db), session_id: str = Depends(get_session_id)
):
    # Ownership check: a foreign id is indistinguishable from a missing one
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.session_id == session_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_documents(db, [doc.id])
    return {"deleted": 1}


@router.delete("/documents")
async def clear_documents(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    ids = [i for (i,) in db.query(Document.id).filter(Document.session_id == session_id).all()]
    return {"deleted": delete_documents(db, ids)}

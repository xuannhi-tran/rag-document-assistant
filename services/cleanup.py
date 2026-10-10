import asyncio
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app import config
from app.database import SessionLocal
from app.models import Chunk, Document


def delete_documents(db: Session, doc_ids: list[int]) -> int:
    """Delete documents and their chunks (chunks first: the FK has no cascade
    on databases created before this change)."""
    if not doc_ids:
        return 0
    db.query(Chunk).filter(Chunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
    n = db.query(Document).filter(Document.id.in_(doc_ids)).delete(synchronize_session=False)
    db.commit()
    return n


def purge_expired(db: Session, hours: int | None = None) -> int:
    """Remove session documents older than the retention window.
    Legacy rows (session_id IS NULL) are left for the manual cleanup in app/purge.py."""
    hours = config.RETENTION_HOURS if hours is None else hours
    ids = [
        i
        for (i,) in db.query(Document.id)
        .filter(Document.session_id.isnot(None))
        .filter(Document.upload_date < func.now() - timedelta(hours=hours))
        .all()
    ]
    return delete_documents(db, ids)


async def purge_loop():
    while True:
        try:
            db = SessionLocal()
            try:
                n = purge_expired(db)
                if n:
                    print(f"[cleanup] purged {n} expired documents")
            finally:
                db.close()
        except Exception as e:  # never let the loop die
            print(f"[cleanup] purge failed: {e}")
        await asyncio.sleep(config.PURGE_INTERVAL_MINUTES * 60)

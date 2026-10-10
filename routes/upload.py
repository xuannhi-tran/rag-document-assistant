import logging
import os
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.deps import get_session_id, get_client_ip
from app.models import Document
from app.services.ingestion import process_pdf
from app.services.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


def _display_name(raw: str | None) -> str:
    name = Path((raw or "document.pdf").replace("\\", "/")).name
    name = re.sub(r"[^\w .()\-\[\]]", "_", name).strip() or "document.pdf"
    return name[:120]


@router.post("/upload/")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    limiter.check(f"upload-ip:{get_client_ip(request)}", config.UPLOADS_PER_HOUR_IP, 3600, "uploads")

    display_name = _display_name(file.filename)
    if not display_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed")

    count = db.query(Document).filter(Document.session_id == session_id).count()
    if count >= config.MAX_FILES_PER_SESSION:
        raise HTTPException(
            status_code=409,
            detail=f"Limit reached: at most {config.MAX_FILES_PER_SESSION} files per session. Remove one first.",
        )

    # Read with a hard cap so an oversized upload is never fully buffered
    contents = await file.read(config.MAX_FILE_BYTES + 1)
    if len(contents) > config.MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {config.MAX_FILE_MB} MB)")
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    # Random temp name: never collides with (or exposes) another visitor's upload
    fd, tmp_name = tempfile.mkstemp(suffix=".pdf", prefix="upload_")
    temp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(contents)

        try:
            pages = len(PdfReader(str(temp_path)).pages)
        except Exception:
            raise HTTPException(status_code=400, detail="File is not a readable PDF")
        if pages > config.MAX_PDF_PAGES:
            raise HTTPException(status_code=413, detail=f"PDF has too many pages (max {config.MAX_PDF_PAGES})")

        try:
            doc = process_pdf(
                str(temp_path), db, session_id=session_id,
                filename=display_name, size_bytes=len(contents),
            )
        except Exception:
            logger.exception("Failed to process uploaded PDF")
            raise HTTPException(status_code=500, detail="The PDF could not be processed")
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "filename": display_name,
        "document_id": doc.id if doc else None,
        "summary": doc.summary if doc else None,
        "status": "processed",
    }
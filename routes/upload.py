import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ingestion import process_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    safe_filename = Path(file.filename).name
    temp_file_path = UPLOAD_DIR / f"{uuid4()}_{safe_filename}"

    try:
        contents = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
        if len(contents) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="PDF exceeds the 10 MB upload limit",
            )

        temp_file_path.write_bytes(contents)
        doc = process_pdf(str(temp_file_path), db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to process uploaded PDF")
        raise HTTPException(
            status_code=500,
            detail="The PDF could not be processed",
        )
    finally:
        temp_file_path.unlink(missing_ok=True)

    return {
        "filename": safe_filename,
        "document_id": doc.id if doc else None,
        "summary": doc.summary if doc else None,
        "status": "processed",
    }

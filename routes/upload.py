from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from app.database import get_db
from app.services.ingestion import process_pdf

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file extension
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed")

    # Save file to temporary directory
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_file_path, "wb") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Process the PDF
    try:
        doc = process_pdf(str(temp_file_path), db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    finally:
        # Clean up the temporary file
        temp_file_path.unlink(missing_ok=True)

    # Return response
    return {
        "filename": file.filename,
        "document_id": doc.id if doc else None,
        "summary": doc.summary if doc else None,
        "status": "processed"
    }
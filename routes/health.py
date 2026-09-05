import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        logger.exception("Health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")

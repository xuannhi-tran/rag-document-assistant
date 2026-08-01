from fastapi import APIRouter
from app.database import get_db
from fastapi import Depends
from sqlalchemy import text

router  = APIRouter()

@router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))  # Simple query to test the connection
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


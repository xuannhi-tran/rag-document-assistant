from fastapi import APIRouter, Depends
from app.schemas import AskRequest
from app.services.retrieval import retrieve_chunks
from app.services.llm import generate_answer
from app.database import get_db


router = APIRouter()

@router.post("/ask")
async def ask(request: AskRequest, db=Depends(get_db)):
    chunks = retrieve_chunks(request.question, db)
    answer = generate_answer(request.question, chunks)
    return {"answer": answer}

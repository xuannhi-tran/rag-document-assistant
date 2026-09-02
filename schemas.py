from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    question: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
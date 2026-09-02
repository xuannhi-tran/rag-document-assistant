from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    question: str
    document_id: Optional[int] = None
    document_ids: Optional[list[int]] = None
    filename: Optional[str] = None
    document_names: Optional[list[str]] = None

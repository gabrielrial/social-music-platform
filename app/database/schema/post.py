from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    content: str
    created_at: datetime
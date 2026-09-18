from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum

"""
class CommentCreate(BaseModel):
    id: str
    author: str
    content: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str
    author: str
    content: str
    post_id: str
    created_at: datetime
"""
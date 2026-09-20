from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.database.models.post import PostType


class PostCreate(BaseModel):
    title: str
    content: str
    post_type: PostType

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    content: str
    post_type: PostType
    created_at: datetime

class PostComment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    content: str
    post_type: PostType
    created_at: datetime
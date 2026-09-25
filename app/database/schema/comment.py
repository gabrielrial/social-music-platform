from datetime import datetime
from app.database.schema.user import XUser
from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    content: str
    post_id: int
    created_at: datetime


class XCommentResponse(BaseModel):

	id: int
	content: str
	created_at: datetime
	author: XUser

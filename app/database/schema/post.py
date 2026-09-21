from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.database.models.post import PostType
from app.database.schema.genre import GenreResponse


class PostCreate(BaseModel):
    title: str
    content: str
    post_type: PostType
    genre_ids: list[int] = []

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    content: str
    post_type: PostType
    created_at: datetime
    genres: list[GenreResponse]

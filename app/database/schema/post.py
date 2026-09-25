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
    like_count: int
    liked_by_me: bool
    rating_avg: float | None  # None (null) when nobody has rated the post
    rating_count: int
    my_rating: int | None  # None when I haven't rated it or I'm anonymous


class LikeStatus(BaseModel):
    """Response of POST/DELETE /posts/{id}/like: enough for a client to
    update the heart icon and the counter without reloading the post."""

    post_id: int
    like_count: int
    liked_by_me: bool

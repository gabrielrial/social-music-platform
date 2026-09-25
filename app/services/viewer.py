from sqlalchemy.orm import Session

from app.database.models.post import Post
from app.database.models.user import User
from app.services.likes import mark_liked_by
from app.services.rating import mark_rated_by


def mark_viewer_state(db: Session, posts: list[Post], user: User | None) -> list[Post]:
    """Fill every per-viewer field of PostResponse (liked_by_me, my_rating).

    The routers call this single function, so a new per-viewer field only has
    to be added here and not in every endpoint that returns posts. Cost: one
    query per field for the whole list, never one per post.
    """
    mark_liked_by(db, posts, user)
    mark_rated_by(db, posts, user)
    return posts

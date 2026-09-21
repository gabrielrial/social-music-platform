from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.models.like import Like
from app.database.models.post import Post
from app.database.models.user import User


def add_like(db: Session, user_id: int, post_id: int) -> None:
    """Idempotent: liking twice leaves a single like.

    INSERT ... ON CONFLICT DO NOTHING lets the primary key do the work. A
    "check first, then insert" in Python would have a race: two requests at
    the same time both see "no like yet" and the second INSERT fails.
    """
    db.execute(
        insert(Like).values(user_id=user_id, post_id=post_id).on_conflict_do_nothing()
    )
    db.commit()


def remove_like(db: Session, user_id: int, post_id: int) -> None:
    """Idempotent: removing a like that does not exist is not an error."""
    db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).delete()
    db.commit()


def count_likes(db: Session, post_id: int) -> int:
    return db.query(func.count()).select_from(Like).filter(Like.post_id == post_id).scalar()


def mark_liked_by(db: Session, posts: list[Post], user: User | None) -> list[Post]:
    """Fill post.liked_by_me for the given user, with ONE query for the whole
    list (not one per post). Anonymous requests get False everywhere."""
    if user is None or not posts:
        return posts

    liked_ids = {
        post_id
        for (post_id,) in db.query(Like.post_id).filter(
            Like.user_id == user.id,
            Like.post_id.in_([p.id for p in posts]),
        )
    }
    for post in posts:
        post.liked_by_me = post.id in liked_ids
    return posts

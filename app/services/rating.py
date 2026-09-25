from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.models.post import Post
from app.database.models.rating import Rating
from app.database.models.user import User


def set_rating(db: Session, user_id: int, post_id: int, score: int) -> None:
    """Create or replace my rating (an "upsert").

    INSERT ... ON CONFLICT DO UPDATE lets the primary key do the work, like
    add_like does with DO NOTHING. A "check first, then insert" in Python
    would have a race: two PUTs at the same time both see "no rating yet",
    both INSERT, and the second one fails with an IntegrityError (500).
    """
    stmt = insert(Rating).values(user_id=user_id, post_id=post_id, score=score)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Rating.user_id, Rating.post_id],
        set_={"score": stmt.excluded.score},
    )
    db.execute(stmt)
    db.commit()


def remove_rating(db: Session, user_id: int, post_id: int) -> None:
    """Idempotent: removing a rating that does not exist is not an error."""
    db.query(Rating).filter(Rating.user_id == user_id, Rating.post_id == post_id).delete()
    db.commit()


def rating_stats(db: Session, post_id: int) -> tuple[float | None, int]:
    """(average rounded to 1 decimal or None, number of ratings) in ONE query.
    Same SQL as Post.rating_avg / Post.rating_count."""
    avg, count = (
        db.query(func.round(func.avg(Rating.score), 1), func.count(Rating.user_id))
        .filter(Rating.post_id == post_id)
        .one()
    )
    return (float(avg) if avg is not None else None), count


def get_my_rating(db: Session, user_id: int, post_id: int) -> int | None:
    return (
        db.query(Rating.score)
        .filter(Rating.user_id == user_id, Rating.post_id == post_id)
        .scalar()
    )


def mark_rated_by(db: Session, posts: list[Post], user: User | None) -> list[Post]:
    """Fill post.my_rating for the given user, with ONE query for the whole
    list (not one per post: 20 posts = 1 query, not 20). Anonymous requests
    keep the default None."""
    if user is None or not posts:
        return posts

    my_scores = dict(
        db.query(Rating.post_id, Rating.score).filter(
            Rating.user_id == user.id,
            Rating.post_id.in_([p.id for p in posts]),
        )
    )
    for post in posts:
        post.my_rating = my_scores.get(post.id)
    return posts

"""
Queries behind the /home feeds. The routers only handle HTTP (auth,
pagination parameters); the "which posts, in which order" lives here.

Every feed:
  - loads the genres of all posts in ONE extra query (selectinload), instead
    of one query per post when the response is serialized (N+1);
  - has a stable order: created_at can tie, so Post.id breaks the tie. Without
    it, offset pagination could show a post twice or skip it.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Query, Session, selectinload

from app.database.models.genre import post_genres, user_genres
from app.database.models.like import Like
from app.database.models.post import Post
from app.database.models.user import User


def _posts(db: Session) -> Query:
    return db.query(Post).options(selectinload(Post.genres))


def _page(query: Query, limit: int, offset: int) -> list[Post]:
    return query.limit(limit).offset(offset).all()


def _genres_of(user: User):
    """Subquery: ids of the genres the user follows."""
    return select(user_genres.c.genre_id).where(user_genres.c.user_id == user.id)


def _shared_genres(user: User):
    """For each post: how many of its genres the user follows.
    A correlated subquery: it is evaluated once per row of `posts`."""
    return (
        select(func.count())
        .select_from(post_genres)
        .where(
            post_genres.c.post_id == Post.id,
            post_genres.c.genre_id.in_(_genres_of(user)),
        )
        .correlate(Post)
        .scalar_subquery()
    )


def _new_genres(user: User):
    """For each post: how many of its genres the user does NOT follow."""
    return (
        select(func.count())
        .select_from(post_genres)
        .where(
            post_genres.c.post_id == Post.id,
            post_genres.c.genre_id.not_in(_genres_of(user)),
        )
        .correlate(Post)
        .scalar_subquery()
    )


# ------------------------------------------------------------------ feeds


def latest(db: Session, limit: int, offset: int) -> list[Post]:
    query = _posts(db).order_by(Post.created_at.desc(), Post.id.desc())
    return _page(query, limit, offset)


def popular(
    db: Session, limit: int, offset: int, days: int, exclude_author: User | None = None
) -> list[Post]:
    """Most liked in the last `days` days. Posts without recent likes still
    show up, at the end, so the feed is never empty."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    recent_likes = (
        select(func.count())
        .select_from(Like)
        .where(Like.post_id == Post.id, Like.created_at >= since)
        .correlate(Post)
        .scalar_subquery()
    )
    query = _posts(db)
    if exclude_author is not None:
        query = query.filter(Post.author_id != exclude_author.id)
    query = query.order_by(recent_likes.desc(), Post.created_at.desc(), Post.id.desc())
    return _page(query, limit, offset)


def recommended(db: Session, user: User, limit: int, offset: int, days: int) -> list[Post]:
    """Posts that share at least one genre with the user, not written by them.
    The more genres in common, the higher; then newest first.

    A user who has not picked any genres gets the popular feed instead."""
    if not user.genres:
        return popular(db, limit, offset, days, exclude_author=user)

    shared = _shared_genres(user)
    query = (
        _posts(db)
        .filter(Post.author_id != user.id, shared > 0)
        .order_by(shared.desc(), Post.created_at.desc(), Post.id.desc())
    )
    return _page(query, limit, offset)


def discover(db: Session, user: User, limit: int, offset: int) -> list[Post]:
    """Posts with at least one genre the user does not follow, not written
    by them. "Bridge" posts come first: they also share a genre with the user
    (rock + jazz for someone who only likes rock), an easy way in."""
    is_bridge = case((_shared_genres(user) > 0, 1), else_=0)
    query = (
        _posts(db)
        .filter(Post.author_id != user.id, _new_genres(user) > 0)
        .order_by(is_bridge.desc(), Post.created_at.desc(), Post.id.desc())
    )
    return _page(query, limit, offset)

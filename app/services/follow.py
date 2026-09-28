"""Queries behind the follow endpoints. The router checks the HTTP rules
(login, 404, can't follow yourself); the "which rows" lives here."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.models.follow import Follow
from app.database.models.user import User


def follow(db: Session, follower_id: int, following_id: int) -> None:
    """Idempotent: following twice leaves a single row.

    INSERT ... ON CONFLICT DO NOTHING lets the primary key do the work, like
    add_like(). "Check first, then insert" would race with a second request."""
    db.execute(
        insert(Follow)
        .values(follower_id=follower_id, following_id=following_id)
        .on_conflict_do_nothing()
    )
    db.commit()


def unfollow(db: Session, follower_id: int, following_id: int) -> None:
    """Idempotent: unfollowing someone you don't follow is not an error."""
    db.query(Follow).filter(
        Follow.follower_id == follower_id, Follow.following_id == following_id
    ).delete()
    db.commit()


def followers(db: Session, user: User, limit: int, offset: int) -> list[User]:
    """Users who follow `user`, most recent follow first."""
    return (
        db.query(User)
        .join(Follow, Follow.follower_id == User.id)  # the User is the one who follows
        .filter(Follow.following_id == user.id)  # this user
        .order_by(Follow.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def following(db: Session, user: User, limit: int, offset: int) -> list[User]:
    """Users that `user` follows, most recent follow first."""
    return (
        db.query(User)
        .join(Follow, Follow.following_id == User.id)  # the User is the one followed
        .filter(Follow.follower_id == user.id)  # by this user
        .order_by(Follow.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

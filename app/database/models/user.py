from sqlalchemy import Column, DateTime, Integer, String, func, select
from sqlalchemy.orm import column_property, relationship

from app.database.conf.alch_conf import Base
from app.database.models.follow import Follow


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String, unique=True, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    # Genres the user likes. `secondary` points to the association table
    # (declared in models/genre.py): SQLAlchemy inserts and deletes its rows
    # when this list changes.
    genres = relationship("Genre", secondary="user_genres", order_by="Genre.name")

    # ------------------------------------------------------------ follows

    # COUNT subqueries, like Post.like_count, but `deferred`: a normal SELECT
    # of users (login, get_current_user, GET /users/) does not compute them.
    # They are loaded the first time one of them is read, and both come
    # together because they share the same `group`. GET /users/{id} asks for
    # them up front with undefer_group("follow_counts"), so it is one query.
    followers_count = column_property(
        select(func.count())
        .select_from(Follow)
        .where(Follow.following_id == id)  # they follow me
        .correlate_except(Follow)
        .scalar_subquery(),
        deferred=True,
        group="follow_counts",
    )

    following_count = column_property(
        select(func.count())
        .select_from(Follow)
        .where(Follow.follower_id == id)  # I follow them
        .correlate_except(Follow)
        .scalar_subquery(),
        deferred=True,
        group="follow_counts",
    )

    # The Follow ROWS on each side (not the users). Two relationships to the
    # same table need `foreign_keys` to say which column each one uses; that is
    # why this is harder than user_genres, where there is only one FK to users.
    # They exist for the cascade: db.delete(user) also deletes their follows.
    # passive_deletes=True lets the database do it (ondelete="CASCADE")
    # instead of loading every row first.
    following_links = relationship(
        Follow,
        foreign_keys=[Follow.follower_id],
        backref="follower",  # Follow.follower -> User
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    follower_links = relationship(
        Follow,
        foreign_keys=[Follow.following_id],
        backref="followed",  # Follow.followed -> User
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

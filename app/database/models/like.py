from sqlalchemy import Column, DateTime, ForeignKey, func
from app.database.conf.alch_conf import Base


class Like(Base):
    """A user likes a post.

    The primary key is the pair (user_id, post_id): the database itself
    rejects a second like from the same user on the same post, so there is
    no need to check for duplicates in Python.

    It is a model class (not a plain Table like user_genres) because it has
    its own data: created_at, which the popular feed needs.
    """

    __tablename__ = "likes"

    user_id = Column(ForeignKey("users.id"), primary_key=True)
    post_id = Column(ForeignKey("posts.id"), primary_key=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy import select
from sqlalchemy.orm import relationship, column_property
from app.database.conf.alch_conf import Base
from sqlalchemy import func
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum
from app.database.models.like import Like


class PostType(str, Enum):
    ALBUM = "album"
    SONG = "song"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    author = relationship("User", back_populates="posts")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post_type = Column(SQLEnum(PostType), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )

    genres = relationship("Genre", secondary="post_genres", order_by="Genre.name")

    # Deleting a post deletes its likes (same ORM cascade as comments).
    likes = relationship(Like, cascade="all, delete-orphan")

    # Not a real column: a COUNT subquery that SQLAlchemy adds to every
    # SELECT of posts. The count comes in the same query, without loading
    # the likes themselves.
    like_count = column_property(
        select(func.count(Like.user_id))
        .where(Like.post_id == id)
        .correlate_except(Like)
        .scalar_subquery()
    )

    # Not stored anywhere: it depends on who is asking. The routers fill it
    # per request with services.likes.mark_liked_by(); False by default.
    liked_by_me = False

    

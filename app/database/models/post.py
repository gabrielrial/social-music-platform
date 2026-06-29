from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.conf.alch_conf import Base
from sqlalchemy import func
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum


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

    #comments = relationship("Comment", backref="post", cascade="all, delete-orphan")

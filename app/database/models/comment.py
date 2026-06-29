from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.conf.alch_conf import Base
from sqlalchemy import func


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)

    author = relationship("User", back_populates="comments")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    #post = relationship("Post", back_populates="comments")


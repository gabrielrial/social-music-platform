from app.database.conf.alch_conf import Base
from sqlalchemy import Column, Integer, DateTime,ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.models.user import User


class FollowUser(Base):
    __tablename__ = "follows"

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
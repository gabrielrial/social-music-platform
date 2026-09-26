from app.database.conf.alch_conf import Base
from sqlalchemy import Column, Integer, DateTime,ForeignKey, func, CheckConstraint
from sqlalchemy.orm import relationship


class Follow(Base):
    __tablename__ = "follows"

    __table_args__ = (
        CheckConstraint("follower_id != following_id", name="prevent_self_follow"),
    )

    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, func

from app.database.conf.alch_conf import Base


class Follow(Base):
    """`follower_id` follows `following_id`.

    Same shape as Like, but both columns point to `users`:
      - the primary key (follower_id, following_id) makes the database reject
        a second follow of the same pair, and its index also serves "who do I
        follow" (follower_id is its first column);
      - `following_id` has its own index for "who follows me", which the
        primary key cannot serve because it is its second column;
      - the CheckConstraint keeps the "no self-follow" rule in the database
        too, not only in the router;
      - ondelete="CASCADE": deleting a user deletes their follows in both
        directions, even when the DELETE does not go through the ORM.
    """

    __tablename__ = "follows"

    __table_args__ = (
        CheckConstraint("follower_id != following_id", name="prevent_self_follow"),
    )

    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    following_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

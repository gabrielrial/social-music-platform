from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, func
from app.database.conf.alch_conf import Base


class Rating(Base):
    """A user rates a post from 1 to 5 stars.

    Same shape as Like: doble primary key (user_id, post_id) makes the database
    itself reject a second rating from the same user on the same post.
    """

    __tablename__ = "ratings"

    # The 1..5 rule lives in the database too, not only in the Pydantic
    # schema: a script, a seed or another service that INSERTs directly
    # cannot store a 0 or a 7.
    __table_args__ = (
        CheckConstraint("score BETWEEN 1 AND 5", name="ck_ratings_score_1_5"),
    )

    user_id = Column(ForeignKey("users.id"), primary_key=True)
    
    # index: Most of the querys look for post.id
    post_id = Column(ForeignKey("posts.id"), primary_key=True, index=True)

    score = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import func
from app.database.conf.alch_conf import Base
from sqlalchemy.orm import relationship
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

    following = relationship(
        Follow,
        foreign_keys=[Follow.follower_id],
        backref="follower",  # Follow.follower -> User
        cascade="all, delete-orphan",
    )
    followers = relationship(
        Follow,
        foreign_keys=[Follow.following_id],
        backref="followed",  # Follow.followed -> User
        cascade="all, delete-orphan",
    )
    

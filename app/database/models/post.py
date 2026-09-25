from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy import select
from sqlalchemy.orm import relationship, column_property
from app.database.conf.alch_conf import Base
from sqlalchemy import func
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum
from app.database.models.like import Like
from app.database.models.rating import Rating


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

    # Deleting a post deletes its ratings
    ratings = relationship(Rating, cascade="all, delete-orphan")


    # Counts the amount of users (user_id) that rated a post (post_id)
    rating_count = column_property(
        select(func.count(Rating.user_id))
        .where(Rating.post_id == id)
        .correlate_except(Rating)
        .scalar_subquery()
    )

    # AVG of zero rows is NULL, so a post nobody has rated gets None (-> null
    # in JSON) without any special case. In Postgres AVG(integer) returns
    # numeric, and round(numeric, 1) exists (round(double, int) does not).
    # Python receives a Decimal; PostResponse turns it into a float.
    rating_avg = column_property(
        select(func.round(func.avg(Rating.score), 1))
        .where(Rating.post_id == id)
        .correlate_except(Rating)
        .scalar_subquery()
    )

    # Not stored anywhere: they depend on who is asking. The routers fill
    # them per request with services.viewer.mark_viewer_state() (one query
    # for the whole list); these are the defaults for anonymous users.
    liked_by_me = False
    my_rating = None

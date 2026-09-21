from sqlalchemy import Column, Integer, String, Table, ForeignKey
from app.database.conf.alch_conf import Base


class Genre(Base):
    """Catalog of music genres.

    A table instead of a Postgres Enum: adding a genre is an INSERT, while
    adding a value to an Enum needs a schema migration.
    """

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

user_genres = Table(
    "user_genres",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

post_genres = Table(
    "post_genres",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

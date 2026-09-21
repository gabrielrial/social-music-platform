from sqlalchemy import Column, Integer, String
from app.database.conf.alch_conf import Base


class Genre(Base):
    """Catalog of music genres.

    A table instead of a Postgres Enum: adding a genre is an INSERT, while
    adding a value to an Enum needs a schema migration.
    """

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

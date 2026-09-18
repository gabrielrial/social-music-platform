from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String


class Base(DeclarativeBase):
    pass


class Genre(Base):
    __tablename__ = "genres"

    genre_id = Column(Integer, primary_key=True)
    genre = Column(String, nullable=False, unique=True)
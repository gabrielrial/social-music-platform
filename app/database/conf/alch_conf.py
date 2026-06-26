# Connecting SQLAlchemy to the PostgreSQL database.

# SQLA, is a Python Library that allows you to interacr with the database using Python code instead of SQL quieres.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# We define the database URL, which contains the connection details for our PostgreSQL database.
DATABASE_URL = "postgresql://admin:password@localhost:5432/forumdb" 

#  Makes the connection to the database
engine = create_engine(DATABASE_URL) 

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

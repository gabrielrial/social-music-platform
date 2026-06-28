from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import func
from app.database.conf.alch_conf import Base
from sqlalchemy.orm import relationship

# Models represent database tables. Each model defines the structure of a
# specific table, including its columns, data types, relationships,
# and whether fields are required or optional.


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

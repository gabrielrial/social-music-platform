from sqlalchemy.orm import Session
from app.database.conf.sqla_conf import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
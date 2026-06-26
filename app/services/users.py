from app.database.models.user import User
from sqlalchemy.orm import Session

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
    
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

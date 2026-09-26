from sqlalchemy.orm import Session
from app.database.models.follow import Follow

def unfollow(db: Session, follower: int, following: int):
    db.query(Follow).filter(Follow.follower_id == follower, Follow.following_id == following).delete()
    db.commit
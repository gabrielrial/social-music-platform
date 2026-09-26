from sqlalchemy.orm import Session
from app.database.models.follow_user import FollowUser

def unfollow(db: Session, follower: int, following: int):
    db.query(FollowUser).filter(FollowUser.follower_id == follower, FollowUser.following_id == following).delete()
    db.commit
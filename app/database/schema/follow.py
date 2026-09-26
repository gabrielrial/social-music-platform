from pydantic import BaseModel
from app.database.schema.user import UserPublic

class CreateFollow(BaseModel):
    follower: int
    following: int

class FollowResponse(BaseModel):
    follower: UserPublic
    following: UserPublic
from pydantic import BaseModel, ConfigDict
# The schemas is how objecros will come from database.

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserResponse):
    """GET /users/{id}: UserResponse plus the follow counters.

    A separate schema so that only this endpoint reads the counters. If they
    were in UserResponse, GET /users/ would load them once per user (N+1)
    and /me, /signup would run extra queries nobody asked for."""

    followers_count: int
    following_count: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str

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

class UserLogin(BaseModel):
    username: str
    password: str
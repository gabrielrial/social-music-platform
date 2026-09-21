from pydantic import BaseModel, ConfigDict


class GenreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class GenreIds(BaseModel):
    genre_ids: list[int]

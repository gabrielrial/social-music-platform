from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    """
    Body of PUT /posts/{id}/rating.

    strict=True: only a real JSON integer is accepted. Without it Pydantic
    would also accept 4.0 or "4" and turn them into 4; 3.5 is rejected either
    way. ge/le give the 422 for 0 or 6 before our code runs.
    """
    score: int = Field(strict=True, ge=1, le=5)


class RatingStatus(BaseModel):
    """Response of PUT/DELETE /posts/{id}/rating: enough for a client to
    update the stars and the average without reloading the post (same idea
    as LikeStatus)."""

    post_id: int
    rating_avg: float | None
    rating_count: int
    my_rating: int | None

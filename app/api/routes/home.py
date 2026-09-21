from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.conf.dependencies import get_db
from app.database.models.user import User
from app.database.schema.post import PostResponse
from app.services import feed
from app.services.auth import get_current_user, get_optional_user
from app.services.likes import mark_liked_by

router = APIRouter(prefix="/home", tags=["home"])


class Page:
    """Pagination parameters shared by every feed. As a dependency
    (`page: Page = Depends()`), FastAPI reads them from the query string
    (?limit=20&offset=40) and validates them: limit=0 or limit=500 is a 422
    before our code runs."""

    def __init__(
        self,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        self.limit = limit
        self.offset = offset


@router.get("/latest", response_model=list[PostResponse])
def home_latest(
    page: Page = Depends(),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    posts = feed.latest(db, page.limit, page.offset)
    return mark_liked_by(db, posts, user)


@router.get("/popular", response_model=list[PostResponse])
def home_popular(
    page: Page = Depends(),
    days: int = Query(7, ge=1, le=365, description="Count likes from the last N days"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    posts = feed.popular(db, page.limit, page.offset, days)
    return mark_liked_by(db, posts, user)


@router.get("/recommended", response_model=list[PostResponse])
def home_recommended(
    page: Page = Depends(),
    days: int = Query(7, ge=1, le=365, description="Count likes from the last N days"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posts = feed.recommended(db, user, page.limit, page.offset, days)
    return mark_liked_by(db, posts, user)


@router.get("/discover", response_model=list[PostResponse])
def home_discover(
    page: Page = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posts = feed.discover(db, user, page.limit, page.offset)
    return mark_liked_by(db, posts, user)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.conf.dependencies import get_db
from app.database.models.user import User
from app.database.schema.post import PostResponse
from app.services import feed
from app.services.auth import get_current_user, get_optional_user
from app.services.pagination import Page
from app.services.viewer import mark_viewer_state

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/latest", response_model=list[PostResponse])
def home_latest(
    page: Page = Depends(),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    posts = feed.latest(db, page.limit, page.offset)
    return mark_viewer_state(db, posts, user)


@router.get("/popular", response_model=list[PostResponse])
def home_popular(
    page: Page = Depends(),
    days: int = Query(7, ge=1, le=365, description="Count likes from the last N days"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    posts = feed.popular(db, page.limit, page.offset, days)
    return mark_viewer_state(db, posts, user)


@router.get("/recommended", response_model=list[PostResponse])
def home_recommended(
    page: Page = Depends(),
    days: int = Query(7, ge=1, le=365, description="Count likes from the last N days"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posts = feed.recommended(db, user, page.limit, page.offset, days)
    return mark_viewer_state(db, posts, user)


@router.get("/discover", response_model=list[PostResponse])
def home_discover(
    page: Page = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posts = feed.discover(db, user, page.limit, page.offset)
    return mark_viewer_state(db, posts, user)


@router.get("/following", response_model=list[PostResponse])
def home_following(
    page: Page = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    posts = feed.following(db, user, page.limit, page.offset)
    return mark_viewer_state(db, posts, user)

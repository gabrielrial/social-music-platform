from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from app.database.models.post import Post
from app.database.models.user import User
from app.database.models.comment import Comment
from app.database.conf.dependencies import get_db
from app.database.schema.post import PostResponse, PostCreate, LikeStatus
from app.database.schema.comment import XCommentResponse
from app.database.schema.rating import RatingCreate, RatingStatus
from app.services.auth import get_current_user, get_optional_user
from app.services.likes import add_like, remove_like, count_likes
from app.services.rating import set_rating, remove_rating, rating_stats, get_my_rating
from app.services.viewer import mark_viewer_state
from app.services.genres import get_genres_by_ids

router = APIRouter(prefix="/posts", tags=["posts"])


class Pagi:
    def __init__(self, limit: int = Query(20, ge=1, le=100), offset: int = Query(0,ge=0)):
        self.limit = limit
        self.offset = offset

@router.get("/", response_model=list[PostResponse])
def get_posts(
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)
):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return mark_viewer_state(db, posts, user)


@router.get("/{post_id}/comments", response_model=list[XCommentResponse])
def get_comments_from_post_id(post_id: int, page: Pagi = Depends(), db=Depends(get_db)):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at)
        .limit(page.limit)
        .offset(page.offset)
    )

    return comments

@router.get("/me", response_model=list[PostResponse])
def get_user_posts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.author_id == current_user.id).all()

    return mark_viewer_state(db, post, current_user)


@router.get("/{post_id}", response_model=PostResponse)
def get_id(
    post_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    mark_viewer_state(db, [post], user)
    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id,
        post_type=post_data.post_type,
        genres=get_genres_by_ids(db, post_data.genre_ids),
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    data: PostCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if user.id != post.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this post",
        )

    post.title = data.title
    post.content = data.content
    post.post_type = data.post_type
    if "genre_ids" in data.model_fields_set:
        post.genres = get_genres_by_ids(db, data.genre_ids)

    db.commit()
    db.refresh(post)

    mark_viewer_state(db, [post], user)
    return post


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if user.id != post.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this post",
        )

    db.delete(post)
    db.commit()


# ------------------------------------------------------------------ likes


def _get_post_or_404(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.post("/{post_id}/like", response_model=LikeStatus)
def like_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_post_or_404(db, post_id)
    add_like(db, user.id, post_id)
    return LikeStatus(
        post_id=post_id, like_count=count_likes(db, post_id), liked_by_me=True
    )


@router.delete("/{post_id}/like", response_model=LikeStatus)
def unlike_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_post_or_404(db, post_id)
    remove_like(db, user.id, post_id)
    return LikeStatus(
        post_id=post_id, like_count=count_likes(db, post_id), liked_by_me=False
    )


# ---------------------------------------------------------------- ratings


def _rating_status(db: Session, post_id: int, user: User) -> RatingStatus:
    avg, count = rating_stats(db, post_id)
    return RatingStatus(
        post_id=post_id,
        rating_avg=avg,
        rating_count=count,
        my_rating=get_my_rating(db, user.id, post_id),
    )


@router.put("/{post_id}/rating", response_model=RatingStatus)
def rate_post(
    post_id: int,
    rating: RatingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PUT, not POST: the client says "my rating for this post IS 4". Sending
    it twice leaves the same state (idempotent) and it replaces the previous
    value, which is exactly what PUT means."""
    post = _get_post_or_404(db, post_id)

    # 403: we know who you are (not 401) and the request is well formed (not
    # 422), but you are not allowed to do this with THIS post.
    if post.author_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can not rate your own post",
        )

    set_rating(db, user.id, post_id, rating.score)
    return _rating_status(db, post_id, user)


@router.delete("/{post_id}/rating", response_model=RatingStatus)
def unrate_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Removes my rating. Idempotent: if I had not rated the post it is not an
    error, the answer is the same 200 (like DELETE /like)."""
    _get_post_or_404(db, post_id)
    remove_rating(db, user.id, post_id)
    return _rating_status(db, post_id, user)

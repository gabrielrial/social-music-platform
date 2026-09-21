from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database.schema.comment import CommentResponse, CommentCreate
from app.database.models.comment import Comment
from app.database.schema.user import UserResponse
from app.database.models.user import User
from app.database.models.post import Post
from app.services.auth import get_current_user
from app.database.conf.dependencies import get_db

router = APIRouter(prefix="/comment", tags=["comments"])


@router.get("/", response_model=list[CommentResponse])
def get_comments(db: Session = Depends(get_db)):
    comments = db.query(Comment).order_by(Comment.created_at.desc()).all()
    return comments


@router.get("/me", response_model=list[CommentResponse])
def get_my_comments(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    comment = db.query(Comment).filter(Comment.author_id == current_user.id).all()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment


@router.post(
    "/post/{post_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    user_comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    comment = Comment(
        author_id=current_user.id,
        content=user_comment.content,
        post_id=post_id,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment

@router.get("/user/{user_id}", response_model=list[CommentResponse], status_code=status.HTTP_200_OK)
def get_comments_from_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    comments = db.query(Comment).filter(Comment.author_id == user.id).order_by(Comment.created_at).all()

    return comments

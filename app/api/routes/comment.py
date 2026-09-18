from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database.schema.comment import CommentResponse
from database.models.comment import Comment
from database.schema.post import PostComment
from database.schema.user import UserResponse
from services.auth import get_current_user
from database.conf.dependencies import get_db



router = APIRouter(prefix="/comment",tags=["comments"])

@router.get("/", response_model=list[CommentResponse])
def get_comments(db: Session = Depends(get_db)):
    comments = db.query(Comment).order_by(Comment.created_at.desc()).all()
    return comments

@router.get("/{comment_id}", response_model=PostComment)
async def get_comment(comment_id: int, db: Session = Depends(get_db)):

    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment
    
@router.get("/me", response_model=list[PostComment])
async def get_comment(current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)):
    
    comment = db.query(Comment).filter(Comment.author_id == current_user.id).all()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment
    
# Comments from a specific user?
#@router.get("/{user_id}", response_model=list[PostComment])

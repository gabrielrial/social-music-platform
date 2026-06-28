from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database.models.post import Post
from app.database.conf.dependencies import get_db
from app.database.schema.post import PostResponse, PostCreate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/{post_id}", response_model=PostResponse)
def get_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.get("/{post_id}", response_model=PostResponse)
def get_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post_data: PostCreate, db: Session = Depends(get_db)):
    new_post = Post(title=post_data.title, content=post_data.content, author_id=2)

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post

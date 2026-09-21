from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database.models.post import Post
from app.database.models.user import User
from app.database.conf.dependencies import get_db
from app.database.schema.post import PostResponse, PostCreate
from app.services.auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=list[PostResponse])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return posts


@router.get("/me", response_model=list[PostResponse])
def get_user_posts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.author_id == current_user.id).all()

    return post


@router.get("/{post_id}", response_model=PostResponse)
def get_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

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

    db.commit()
    db.refresh(post)

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

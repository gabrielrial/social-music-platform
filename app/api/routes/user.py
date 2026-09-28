from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, undefer_group
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.security import hash_password, verify_password


from app.database.models.user import User
from app.database.schema.user import UserCreate, UserProfile, UserPublic, UserResponse
from app.database.schema.genre import GenreResponse, GenreIds
from app.database.conf.dependencies import get_db
from app.services import follow as follows
from app.services.auth import get_current_user, create_access_token
from app.services.users import get_user_by_email, get_user_by_username, get_user_or_404
from app.services.genres import get_genres_by_ids
from app.services.pagination import Page

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_users(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(User).all()


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/genres", response_model=list[GenreResponse])
def get_my_genres(current_user: User = Depends(get_current_user)):
    return current_user.genres


@router.put("/me/genres", response_model=list[GenreResponse])
def set_my_genres(
    data: GenreIds,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # PUT replaces the whole list: assigning it makes SQLAlchemy delete the
    # old rows in user_genres and insert the new ones.
    current_user.genres = get_genres_by_ids(db, data.genre_ids)
    db.commit()
    db.refresh(current_user)
    return current_user.genres


@router.get("/{user_id}", response_model=UserProfile)
def get_user(user_id: int, db: Session = Depends(get_db)):
    # The follow counters are deferred (see models/user.py): ask for them
    # here so they come in the same SELECT as the user. One query in total.
    user = (
        db.query(User)
        .options(undefer_group("follow_counts"))
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):

    existing_email = get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    existing_username = get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == form.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    if not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token({"sub": user.username})

    return {"access_token": token, "token_type": "bearer"}

# ---------------------------------------------------------------- follows


@router.put("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PUT, not POST: the client says "I follow user_id" and repeating it
    changes nothing (idempotent). 204 because there is nothing to return.

    Following yourself is a 400: the request is well formed and the user
    exists, but the operation makes no sense. It is not 403 (no permission is
    missing), 404 (the user exists) or 409 (there is no conflicting state).
    The database enforces the same rule with a CheckConstraint."""
    if user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot follow yourself")
    get_user_or_404(db, user_id)
    follows.follow(db, user.id, user_id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotent: if I was not following them it is not an error, same 204.
    An unknown user is still a 404, like DELETE /posts/{id}/like."""
    get_user_or_404(db, user_id)
    follows.unfollow(db, user.id, user_id)


# Public lists. They return UserPublic (id + username): UserResponse has the
# email, and anyone can read who follows whom.


@router.get("/{user_id}/followers", response_model=list[UserPublic])
def get_followers(user_id: int, page: Page = Depends(), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    return follows.followers(db, user, page.limit, page.offset)


@router.get("/{user_id}/following", response_model=list[UserPublic])
def get_following(user_id: int, page: Page = Depends(), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    return follows.following(db, user, page.limit, page.offset)

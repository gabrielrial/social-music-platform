from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.utils.security import hash_password, verify_password


from app.database.models.user import User
from app.database.schema.user import UserCreate, UserResponse
from app.database.conf.dependencies import get_db
from app.services.auth import get_current_user, create_access_token
from app.services.users import get_user_by_email, get_user_by_username

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 1
SECRET = "70ddbfecf49a1d435674562e4775b9f873962d0e28511203a65a202df88d89c5"


@router.get("/", response_model=list[UserResponse])
def get_users(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(User).all()


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/signup", response_model=UserResponse)
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
async def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):

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

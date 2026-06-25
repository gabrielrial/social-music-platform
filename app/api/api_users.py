from fastapi import APIRouter, HTTPException ,Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.database.utils.security import hash_password, verify_password 


from app.database.models.user import User
from app.database.schema.user import UserCreate, UserResponse
from app.database.conf.dependencies import get_db


router = APIRouter(prefix="/users", tags=["users"])

ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 1
SECRET = "70ddbfecf49a1d435674562e4775b9f873962d0e28511203a65a202df88d89c5"


#@router.post("/", response_model=UserResponse)
#def create_user(user: UserCreate, db: Session = Depends(get_db)):
#    db_user = User(username=user.username, email=user.email, password_hash=user.password)
#    db.add(db_user)
#    db.commit()
#    db.refresh(db_user)
#    return db_user


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):

    existing_email = get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    existing_username = get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    print(type(user.password))
    print(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password) 
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)):

    print("login")
    
    user = db.query(User).filter(
        User.username == form.username
    ).first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(
        form.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_DURATION),
    }

    return {"message": "Login successful"}




def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()
    
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


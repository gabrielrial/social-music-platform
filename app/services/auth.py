from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from app.database.conf.dependencies import get_db
from app.utils.security import SECRET, ALGORITHM, ACCESS_TOKEN_DURATION
from app.services.users import get_user_by_username


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Same scheme, but it does not raise 401 when the header is missing: it
# returns None. For public endpoints that show more if you are logged in.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    return _user_from_token(token, db)


def get_optional_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
):
    """None if there is no token. A token that IS sent but is invalid or
    expired still gives 401, so the client knows it has to log in again
    instead of silently getting the anonymous view."""
    if token is None:
        return None
    return _user_from_token(token, db)


def _user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])

        username: str | None = payload.get("sub")

        if not username:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)

    if not user:
        raise credentials_exception

    return user


def create_access_token(data: dict):
    payload = data.copy()

    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_DURATION
    )

    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)
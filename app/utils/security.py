from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 1
SECRET = "70ddbfecf49a1d435674562e4775b9f873962d0e28511203a65a202df88d89c5"

crypt = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return crypt.hash(password)

def verify_password(password: str, hashed_password: str):
    return crypt.verify(
        password,
        hashed_password
    )
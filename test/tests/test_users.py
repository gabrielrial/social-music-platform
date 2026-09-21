from app.database.models.user import User


# ----------------------------------------------------------------- signup

def test_signup_creates_user(client, seed):
    response = client.post(
        "/users/signup",
        json={"username": "nuevo", "email": "nuevo@test.com", "password": "secreto"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "nuevo"
    assert data["email"] == "nuevo@test.com"
    # The response must never expose the password or its hash
    assert "password" not in data
    assert "password_hash" not in data


def test_signup_duplicate_username(client, seed):
    existing = seed.users[0]
    response = client.post(
        "/users/signup",
        json={"username": existing["username"], "email": "otro@test.com", "password": "x"},
    )
    assert response.status_code == 400


def test_signup_duplicate_email(client, seed):
    existing = seed.users[0]
    response = client.post(
        "/users/signup",
        json={"username": "otro", "email": existing["email"], "password": "x"},
    )
    assert response.status_code == 400


def test_signup_missing_field(client):
    response = client.post("/users/signup", json={"username": "sin_email"})
    assert response.status_code == 422  # Pydantic rejects the body


def test_password_is_stored_hashed(client, db):
    client.post(
        "/users/signup",
        json={"username": "pepe", "email": "pepe@test.com", "password": "123456"},
    )
    user = db.query(User).filter(User.username == "pepe").first()
    assert user is not None
    assert user.password_hash != "123456"


# ---------------------------------------------------------------- login

def test_login_ok(client, seed):
    user = seed.users[3]
    response = client.post(
        "/users/login", data={"username": user["username"], "password": seed.password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, seed):
    response = client.post(
        "/users/login", data={"username": seed.users[0]["username"], "password": "mal"}
    )
    assert response.status_code == 401


def test_login_unknown_user(client, seed):
    response = client.post("/users/login", data={"username": "nadie", "password": "x"})
    assert response.status_code == 401


# --------------------------------------------------------------- /users/me

def test_me_returns_logged_user(client, seed, login):
    user = seed.users[5]
    response = client.get("/users/me", headers=login(user["username"]))
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["username"] == user["username"]


def test_me_without_token(client):
    assert client.get("/users/me").status_code == 401


def test_me_with_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer basura"})
    assert response.status_code == 401


# --------------------------------------------------------- list and detail

def test_list_users_requires_auth(client, seed):
    assert client.get("/users/").status_code == 401


def test_list_users(client, seed, login):
    response = client.get("/users/", headers=login(seed.users[0]["username"]))
    assert response.status_code == 200
    assert len(response.json()) == len(seed.users)  # 10


def test_get_user_by_id(client, seed):
    user = seed.users[2]
    response = client.get(f"/users/{user['id']}")
    assert response.status_code == 200
    assert response.json()["username"] == user["username"]


def test_get_user_not_found(client, seed):
    assert client.get("/users/999999").status_code == 404

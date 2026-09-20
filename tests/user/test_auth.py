from tests.conftest import client

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_signup():
    response = client.post(
        "/users/signup",
        json={
            "username": "pepe",
            "email": "pepe@test.com",
            "password": "123456"
        }
    )

    assert response.status_code == 200
    data = response.json()

    print(response.json())
    assert data["username"] == "pepe"
    assert data["email"] == "pepe@test.com"

def test_login():
    response = client.post(
        "/users/login",
        data={
            "username": "pepe",
            "password": "123456"
        }
    )

    assert response.status_code == 200
    print(response.text)

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_me():
    login = client.post(
        "/users/login",
        data={
            "username": "pepe",
            "password": "123456"
        }
    )

    token = login.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

def test_me_without_token():
    response = client.get("/users/me")

    assert response.status_code == 401

def test_login_wrong_password():
    response = client.post(
        "/users/login",
        data={
            "username": "pepe",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
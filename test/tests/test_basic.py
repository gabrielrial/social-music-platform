def test_root(client):
    response = client.get("/")
    assert response.status_code == 200

def test_wrong_user(client):
    response = client.post("/users/login", data={"username": "user", "password": "password"})
    assert response.status_code == 401


def test_cors_allowed_origin(client):
    """Preflight from an allowed origin: the browser gets permission."""
    response = client.options(
        "/posts/",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8080"


def test_cors_unknown_origin(client):
    """Preflight from an origin that is not in the list: no permission header."""
    response = client.options(
        "/posts/",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers

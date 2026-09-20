def test_root(client):
    response = client.get("/")
    assert response.status_code == 200

def test_wrong_user(client):
    response = client.post("/users/login", data={"username": "user", "password": "password"})
    assert response.status_code == 401
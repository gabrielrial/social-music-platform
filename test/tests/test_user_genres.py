from sqlalchemy import select

from app.database.models.genre import user_genres


def genre_ids(client, *names):
    """Ids of the catalog genres with those names."""
    catalog = {g["name"]: g["id"] for g in client.get("/genres/").json()}
    return [catalog[n] for n in names]


def test_my_genres_start_empty(client, seed, login):
    response = client.get("/users/me/genres", headers=login(seed.users[0]["username"]))
    assert response.status_code == 200
    assert response.json() == []


def test_set_my_genres(client, seed, login):
    headers = login(seed.users[0]["username"])
    ids = genre_ids(client, "rock", "blues")

    response = client.put("/users/me/genres", json={"genre_ids": ids}, headers=headers)
    assert response.status_code == 200
    assert [g["name"] for g in response.json()] == ["blues", "rock"]  # sorted by name

    # And it was saved
    saved = client.get("/users/me/genres", headers=headers).json()
    assert [g["name"] for g in saved] == ["blues", "rock"]


def test_put_replaces_previous_genres(client, seed, login):
    headers = login(seed.users[0]["username"])
    client.put("/users/me/genres", json={"genre_ids": genre_ids(client, "rock", "blues")}, headers=headers)
    client.put("/users/me/genres", json={"genre_ids": genre_ids(client, "jazz")}, headers=headers)

    saved = client.get("/users/me/genres", headers=headers).json()
    assert [g["name"] for g in saved] == ["jazz"]


def test_empty_list_clears_genres(client, seed, login, db):
    user = seed.users[0]
    headers = login(user["username"])
    client.put("/users/me/genres", json={"genre_ids": genre_ids(client, "rock")}, headers=headers)

    response = client.put("/users/me/genres", json={"genre_ids": []}, headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    # No orphan rows left in the association table
    rows = db.execute(select(user_genres).where(user_genres.c.user_id == user["id"])).all()
    assert rows == []


def test_duplicate_ids_are_ignored(client, seed, login):
    headers = login(seed.users[0]["username"])
    [rock] = genre_ids(client, "rock")
    response = client.put("/users/me/genres", json={"genre_ids": [rock, rock]}, headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_unknown_genre_id(client, seed, login):
    headers = login(seed.users[0]["username"])
    client.put("/users/me/genres", json={"genre_ids": genre_ids(client, "rock")}, headers=headers)

    [jazz] = genre_ids(client, "jazz")
    response = client.put("/users/me/genres", json={"genre_ids": [jazz, 999999]}, headers=headers)
    assert response.status_code == 422
    assert "999999" in response.json()["detail"]

    # Nothing changed: the request is all or nothing
    saved = client.get("/users/me/genres", headers=headers).json()
    assert [g["name"] for g in saved] == ["rock"]


def test_genres_are_per_user(client, seed, login):
    me, other = seed.users[0], seed.users[1]
    client.put(
        "/users/me/genres",
        json={"genre_ids": genre_ids(client, "rock")},
        headers=login(me["username"]),
    )
    assert client.get("/users/me/genres", headers=login(other["username"])).json() == []


def test_my_genres_require_auth(client):
    assert client.get("/users/me/genres").status_code == 401
    assert client.put("/users/me/genres", json={"genre_ids": []}).status_code == 401

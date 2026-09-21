from app.database.models.comment import Comment

NEW_POST = {
    "title": "Truth",
    "content": "A solid blues-rock record.",
    "post_type": "album",
}


def other_user(seed, user_id):
    """A seeded user that is NOT user_id."""
    return next(u for u in seed.users if u["id"] != user_id)


# ------------------------------------------------------------------ read


def test_list_posts(client, seed):
    response = client.get("/posts/")
    assert response.status_code == 200
    assert len(response.json()) == len(seed.posts)  # 20


def test_list_posts_newest_first(client, seed):
    dates = [p["created_at"] for p in client.get("/posts/").json()]
    assert dates == sorted(dates, reverse=True)


def test_get_post_by_id(client, seed):
    post = seed.posts[7]
    response = client.get(f"/posts/{post['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == post["title"]
    assert response.json()["author_id"] == post["author_id"]


def test_get_post_not_found(client, seed):
    assert client.get("/posts/999999").status_code == 404


def test_my_posts_only_returns_mine(client, seed, login):
    user = seed.users[0]
    response = client.get("/posts/me", headers=login(user["username"]))
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == len(seed.posts_by(user["id"]))
    assert all(p["author_id"] == user["id"] for p in posts)


def test_my_posts_requires_auth(client):
    assert client.get("/posts/me").status_code == 401


# ---------------------------------------------------------------- create


def test_create_post(client, seed, login):
    user = seed.users[1]
    response = client.post("/posts/", json=NEW_POST, headers=login(user["username"]))
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == NEW_POST["title"]
    assert data["author_id"] == user["id"]  # author comes from the token, not the body
    assert len(client.get("/posts/").json()) == len(seed.posts) + 1


def test_create_post_requires_auth(client, seed):
    assert client.post("/posts/", json=NEW_POST).status_code == 401


def test_create_post_invalid_type(client, seed, login):
    headers = login(seed.users[0]["username"])
    response = client.post(
        "/posts/", json={**NEW_POST, "post_type": "podcast"}, headers=headers
    )
    assert response.status_code == 422


# ---------------------------------------------------------------- update


def test_update_own_post(client, seed, login):
    post = seed.posts[0]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    response = client.patch(
        f"/posts/{post['id']}",
        json={
            "title": "New title",
            "content": "New text",
            "post_type": post["post_type"],
        },
        headers=login(author["username"]),
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_post_type(client, seed, login):
    post = seed.posts[0]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    new_type = "song" if post["post_type"] == "album" else "album"
    response = client.patch(
        f"/posts/{post['id']}",
        json={"title": "t", "content": "c", "post_type": new_type},
        headers=login(author["username"]),
    )
    assert response.json()["post_type"] == new_type


def test_update_other_users_post_forbidden(client, seed, login):
    post = seed.posts[0]
    intruder = other_user(seed, post["author_id"])
    response = client.patch(
        f"/posts/{post['id']}", json=NEW_POST, headers=login(intruder["username"])
    )
    assert response.status_code == 403


def test_update_post_requires_auth(client, seed):
    assert (
        client.patch(f"/posts/{seed.posts[0]['id']}", json=NEW_POST).status_code == 401
    )


def test_update_post_not_found(client, seed, login):
    response = client.patch(
        "/posts/999999", json=NEW_POST, headers=login(seed.users[0]["username"])
    )
    assert response.status_code == 404


# ---------------------------------------------------------------- delete


def test_delete_own_post(client, seed, login):
    post = seed.posts[4]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    response = client.delete(f"/posts/{post['id']}", headers=login(author["username"]))
    assert response.status_code == 204
    assert client.get(f"/posts/{post['id']}").status_code == 404


def test_delete_post_deletes_its_comments(client, seed, login, db):
    post = seed.posts[4]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    client.delete(f"/posts/{post['id']}", headers=login(author["username"]))

    remaining = db.query(Comment).filter(Comment.post_id == post["id"]).count()
    assert remaining == 0  # cascade="all, delete-orphan" on the Post model


def test_delete_other_users_post_forbidden(client, seed, login):
    post = seed.posts[0]
    intruder = other_user(seed, post["author_id"])
    response = client.delete(
        f"/posts/{post['id']}", headers=login(intruder["username"])
    )
    assert response.status_code == 403


def test_delete_post_requires_auth(client, seed):
    assert client.delete(f"/posts/{seed.posts[0]['id']}").status_code == 401

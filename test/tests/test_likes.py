from app.database.models.like import Like


def like(client, post_id, headers):
    return client.post(f"/posts/{post_id}/like", headers=headers)


def unlike(client, post_id, headers):
    return client.delete(f"/posts/{post_id}/like", headers=headers)


# ------------------------------------------------------------ like/unlike


def test_like_post(client, seed, login):
    post_id = seed.posts[0]["id"]
    response = like(client, post_id, login(seed.users[0]["username"]))
    assert response.status_code == 200
    assert response.json() == {"post_id": post_id, "like_count": 1, "liked_by_me": True}


def test_like_twice_is_idempotent(client, seed, login, db):
    post_id = seed.posts[0]["id"]
    headers = login(seed.users[0]["username"])
    like(client, post_id, headers)
    response = like(client, post_id, headers)

    assert response.status_code == 200
    assert response.json()["like_count"] == 1
    assert db.query(Like).filter(Like.post_id == post_id).count() == 1


def test_likes_from_different_users_add_up(client, seed, login):
    post_id = seed.posts[0]["id"]
    for user in seed.users[:3]:
        response = like(client, post_id, login(user["username"]))
    assert response.json()["like_count"] == 3


def test_unlike_post(client, seed, login):
    post_id = seed.posts[0]["id"]
    headers = login(seed.users[0]["username"])
    like(client, post_id, headers)

    response = unlike(client, post_id, headers)
    assert response.status_code == 200
    assert response.json() == {"post_id": post_id, "like_count": 0, "liked_by_me": False}


def test_unlike_without_like_is_idempotent(client, seed, login):
    response = unlike(client, seed.posts[0]["id"], login(seed.users[0]["username"]))
    assert response.status_code == 200
    assert response.json()["like_count"] == 0


def test_unlike_only_removes_my_like(client, seed, login):
    post_id = seed.posts[0]["id"]
    me, other = seed.users[0], seed.users[1]
    like(client, post_id, login(me["username"]))
    like(client, post_id, login(other["username"]))

    response = unlike(client, post_id, login(me["username"]))
    assert response.json()["like_count"] == 1


def test_like_post_not_found(client, seed, login):
    headers = login(seed.users[0]["username"])
    assert like(client, 999999, headers).status_code == 404
    assert unlike(client, 999999, headers).status_code == 404


def test_like_requires_auth(client, seed):
    post_id = seed.posts[0]["id"]
    assert client.post(f"/posts/{post_id}/like").status_code == 401
    assert client.delete(f"/posts/{post_id}/like").status_code == 401


# ------------------------------------------- like_count / liked_by_me on posts


def test_post_shows_like_count_anonymous(client, seed, login):
    post_id = seed.posts[0]["id"]
    like(client, post_id, login(seed.users[0]["username"]))
    like(client, post_id, login(seed.users[1]["username"]))

    data = client.get(f"/posts/{post_id}").json()  # no token
    assert data["like_count"] == 2
    assert data["liked_by_me"] is False


def test_liked_by_me_depends_on_who_asks(client, seed, login):
    post_id = seed.posts[0]["id"]
    liker, other = seed.users[0], seed.users[1]
    like(client, post_id, login(liker["username"]))

    assert client.get(f"/posts/{post_id}", headers=login(liker["username"])).json()["liked_by_me"] is True
    assert client.get(f"/posts/{post_id}", headers=login(other["username"])).json()["liked_by_me"] is False


def test_list_posts_marks_only_my_likes(client, seed, login):
    headers = login(seed.users[0]["username"])
    liked = {seed.posts[0]["id"], seed.posts[5]["id"]}
    for post_id in liked:
        like(client, post_id, headers)

    posts = client.get("/posts/", headers=headers).json()
    assert {p["id"] for p in posts if p["liked_by_me"]} == liked
    assert all(p["like_count"] == (1 if p["id"] in liked else 0) for p in posts)


def test_new_post_has_no_likes(client, seed, login):
    body = {"title": "Truth", "content": "Blues-rock.", "post_type": "album"}
    data = client.post("/posts/", json=body, headers=login(seed.users[0]["username"])).json()
    assert data["like_count"] == 0
    assert data["liked_by_me"] is False


def test_invalid_token_on_public_endpoint_is_401(client, seed):
    # Sending a broken token is not the same as sending none.
    headers = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/posts/", headers=headers).status_code == 401
    assert client.get("/posts/").status_code == 200


def test_delete_post_deletes_its_likes(client, seed, login, db):
    post = seed.posts[4]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    like(client, post["id"], login(seed.users[0]["username"]))

    client.delete(f"/posts/{post['id']}", headers=login(author["username"]))
    assert db.query(Like).filter(Like.post_id == post["id"]).count() == 0

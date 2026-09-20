import pytest

from app.database.models.comment import Comment
from app.database.models.post import Post
from tests.seed import COMMENTS_PER_POST


# ------------------------------------------------------------- seeded data

def test_seed_has_three_comments_per_post(seed, db):
    for post in db.query(Post).all():
        assert db.query(Comment).filter(Comment.post_id == post.id).count() == COMMENTS_PER_POST


# ------------------------------------------------------------------ read

def test_list_comments(client, seed):
    response = client.get("/comment/")
    assert response.status_code == 200
    assert len(response.json()) == len(seed.comments)  # 60


def test_get_comment_by_id(client, seed):
    comment = seed.comments[10]
    response = client.get(f"/comment/{comment['id']}")
    assert response.status_code == 200
    assert response.json()["content"] == comment["content"]
    assert response.json()["post_id"] == comment["post_id"]


def test_get_comment_not_found(client, seed):
    assert client.get("/comment/999999").status_code == 404


def test_my_comments_only_returns_mine(client, seed, login):
    # A seeded user with at least one comment
    user = next(u for u in seed.users if seed.comments_by(u["id"]))
    response = client.get("/comment/me", headers=login(user["username"]))
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) == len(seed.comments_by(user["id"]))
    assert all(c["author_id"] == user["id"] for c in comments)


@pytest.mark.xfail(reason="BUG: /comment/me returns 404 instead of [] when there are none", strict=True)
def test_my_comments_empty_returns_empty_list(client, seed, login):
    client.post(
        "/users/signup",
        json={"username": "quiet", "email": "quiet@test.com", "password": "123456"},
    )
    response = client.get("/comment/me", headers=login("quiet", "123456"))
    assert response.status_code == 200
    assert response.json() == []


def test_my_comments_requires_auth(client):
    assert client.get("/comment/me").status_code == 401


# ---------------------------------------------------------------- create

def test_create_comment(client, seed, login):
    user = seed.users[0]
    post = seed.posts[5]
    response = client.post(
        f"/comment/post/{post['id']}",
        json={"content": "Great review"},
        headers=login(user["username"]),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["post_id"] == post["id"]
    assert data["author_id"] == user["id"]
    assert len(client.get("/comment/").json()) == len(seed.comments) + 1


def test_create_comment_requires_auth(client, seed):
    post = seed.posts[0]
    response = client.post(f"/comment/post/{post['id']}", json={"content": "hello"})
    assert response.status_code == 401


def test_create_comment_on_missing_post(client, seed, login):
    response = client.post(
        "/comment/post/999999",
        json={"content": "hello"},
        headers=login(seed.users[0]["username"]),
    )
    assert response.status_code == 404


def test_create_comment_empty_body(client, seed, login):
    response = client.post(
        f"/comment/post/{seed.posts[0]['id']}",
        json={},
        headers=login(seed.users[0]["username"]),
    )
    assert response.status_code == 422

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from app.database.models.rating import Rating
from test.conf.conf_database import engine


def rate(client, post_id, score, headers):
    return client.put(f"/posts/{post_id}/rating", json={"score": score}, headers=headers)


def unrate(client, post_id, headers):
    return client.delete(f"/posts/{post_id}/rating", headers=headers)


def raters(seed, post, n):
    """n users that are NOT the author of the post (you can't rate your own)."""
    return [u for u in seed.users if u["id"] != post["author_id"]][:n]


# ------------------------------------------------------------ PUT / DELETE


def test_rate_post(client, seed, login):
    post = seed.posts[0]
    [user] = raters(seed, post, 1)
    response = rate(client, post["id"], 4, login(user["username"]))
    assert response.status_code == 200
    assert response.json() == {
        "post_id": post["id"], "rating_avg": 4.0, "rating_count": 1, "my_rating": 4,
    }


def test_example_from_the_exercise(client, seed, login):
    post = seed.posts[0]
    a, b = raters(seed, post, 2)
    rate(client, post["id"], 4, login(a["username"]))

    data = rate(client, post["id"], 2, login(b["username"])).json()
    assert (data["rating_avg"], data["rating_count"], data["my_rating"]) == (3.0, 2, 2)

    # b changes their mind: replaced, not added
    data = rate(client, post["id"], 5, login(b["username"])).json()
    assert (data["rating_avg"], data["rating_count"], data["my_rating"]) == (4.5, 2, 5)


def test_rating_twice_replaces(client, seed, login, db):
    post = seed.posts[0]
    [user] = raters(seed, post, 1)
    headers = login(user["username"])
    rate(client, post["id"], 1, headers)
    rate(client, post["id"], 5, headers)

    rows = db.query(Rating).filter(Rating.post_id == post["id"]).all()
    assert [r.score for r in rows] == [5]


def test_average_is_rounded_to_one_decimal(client, seed, login):
    post = seed.posts[0]
    scores = [5, 4, 4]  # 4.333...
    for user, score in zip(raters(seed, post, 3), scores):
        data = rate(client, post["id"], score, login(user["username"])).json()
    assert data["rating_avg"] == 4.3


@pytest.mark.parametrize("score", [0, 6, 3.5, 4.0, "4", None])
def test_invalid_score_is_422(client, seed, login, score):
    post = seed.posts[0]
    [user] = raters(seed, post, 1)
    assert rate(client, post["id"], score, login(user["username"])).status_code == 422


def test_missing_score_is_422(client, seed, login):
    post = seed.posts[0]
    [user] = raters(seed, post, 1)
    response = client.put(f"/posts/{post['id']}/rating", json={}, headers=login(user["username"]))
    assert response.status_code == 422


def test_rate_post_not_found(client, seed, login):
    headers = login(seed.users[0]["username"])
    assert rate(client, 999999, 3, headers).status_code == 404
    assert unrate(client, 999999, headers).status_code == 404


def test_cannot_rate_own_post(client, seed, login, db):
    post = seed.posts[0]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    assert rate(client, post["id"], 5, login(author["username"])).status_code == 403
    assert db.query(Rating).count() == 0


def test_rating_requires_auth(client, seed):
    post_id = seed.posts[0]["id"]
    assert client.put(f"/posts/{post_id}/rating", json={"score": 3}).status_code == 401
    assert client.delete(f"/posts/{post_id}/rating").status_code == 401


def test_delete_rating(client, seed, login):
    post = seed.posts[0]
    a, b = raters(seed, post, 2)
    rate(client, post["id"], 4, login(a["username"]))
    rate(client, post["id"], 2, login(b["username"]))

    response = unrate(client, post["id"], login(b["username"]))
    assert response.status_code == 200
    assert response.json() == {
        "post_id": post["id"], "rating_avg": 4.0, "rating_count": 1, "my_rating": None,
    }


def test_delete_rating_that_does_not_exist_is_not_an_error(client, seed, login):
    post = seed.posts[0]
    [user] = raters(seed, post, 1)
    response = unrate(client, post["id"], login(user["username"]))
    assert response.status_code == 200
    assert response.json()["rating_count"] == 0
    assert response.json()["rating_avg"] is None


# ------------------------------------------------ fields on PostResponse


def test_post_without_ratings(client, seed):
    data = client.get(f"/posts/{seed.posts[0]['id']}").json()
    assert data["rating_avg"] is None
    assert data["rating_count"] == 0
    assert data["my_rating"] is None


def test_anonymous_sees_average_but_no_my_rating(client, seed, login):
    post = seed.posts[0]
    for user, score in zip(raters(seed, post, 2), [4, 5]):
        rate(client, post["id"], score, login(user["username"]))

    data = client.get(f"/posts/{post['id']}").json()
    assert (data["rating_avg"], data["rating_count"], data["my_rating"]) == (4.5, 2, None)


def test_my_rating_depends_on_who_asks(client, seed, login):
    post = seed.posts[0]
    rater, other = raters(seed, post, 2)
    rate(client, post["id"], 3, login(rater["username"]))

    assert client.get(f"/posts/{post['id']}", headers=login(rater["username"])).json()["my_rating"] == 3
    assert client.get(f"/posts/{post['id']}", headers=login(other["username"])).json()["my_rating"] is None


def test_lists_include_my_rating(client, seed, login):
    user = seed.users[0]
    headers = login(user["username"])
    rated = {p["id"]: i + 1 for i, p in enumerate(
        [p for p in seed.posts if p["author_id"] != user["id"]][:3]
    )}
    for post_id, score in rated.items():
        rate(client, post_id, score, headers)

    for url in ["/posts/", "/home/latest?limit=100"]:
        posts = client.get(url, headers=headers).json()
        assert {p["id"]: p["my_rating"] for p in posts if p["my_rating"] is not None} == rated


def test_list_does_not_run_one_query_per_post(client, seed, login):
    user = seed.users[0]
    headers = login(user["username"])
    for post in [p for p in seed.posts if p["author_id"] != user["id"]][:5]:
        rate(client, post["id"], 4, headers)

    statements = []

    def count(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        posts = client.get("/home/latest?limit=20", headers=headers).json()
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert len(posts) == 20
    # user lookup + posts + genres + likes + ratings: a constant, not 20+.
    assert len(statements) <= 6, statements


# ------------------------------------------------------------ database


def test_database_rejects_score_out_of_range(seed, db):
    post = seed.posts[0]
    user = next(u for u in seed.users if u["id"] != post["author_id"])
    db.add(Rating(user_id=user["id"], post_id=post["id"], score=7))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_delete_post_deletes_its_ratings(client, seed, login, db):
    post = seed.posts[4]
    author = next(u for u in seed.users if u["id"] == post["author_id"])
    [user] = raters(seed, post, 1)
    rate(client, post["id"], 5, login(user["username"]))

    assert client.delete(f"/posts/{post['id']}", headers=login(author["username"])).status_code == 204
    assert db.query(Rating).filter(Rating.post_id == post["id"]).count() == 0

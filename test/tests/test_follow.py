"""
Tests for exercise 4: following users and the /home/following feed.

  - PUT / DELETE /users/{id}/follow
  - GET /users/{id}/followers and /users/{id}/following
  - followers_count / following_count in GET /users/{id}
  - GET /home/following
  - the database rules (no self-follow, no duplicates, cascade on delete)
"""

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from app.database.models.follow import Follow
from app.database.models.user import User
from test.conf.conf_database import engine
from test.conf.seed import seed_follows, seed_social

ALL = {"limit": 100}


def follow(client, user_id, headers):
    return client.put(f"/users/{user_id}/follow", headers=headers)


def unfollow(client, user_id, headers):
    return client.delete(f"/users/{user_id}/follow", headers=headers)


def followers(client, user_id, **params):
    return client.get(f"/users/{user_id}/followers", params=params)


def following(client, user_id, **params):
    return client.get(f"/users/{user_id}/following", params=params)


def usernames(response):
    assert response.status_code == 200, response.text
    return [u["username"] for u in response.json()]


def post_ids(response):
    assert response.status_code == 200, response.text
    return [p["id"] for p in response.json()]


def follow_rows(db, follower_id=None, following_id=None):
    query = db.query(Follow)
    if follower_id is not None:
        query = query.filter(Follow.follower_id == follower_id)
    if following_id is not None:
        query = query.filter(Follow.following_id == following_id)
    return query.count()


class QueryCounter:
    """Counts the SQL statements sent to the test database inside a `with`."""

    def __enter__(self):
        self.statements = []
        event.listen(engine, "before_cursor_execute", self._count)
        return self

    def __exit__(self, *exc):
        event.remove(engine, "before_cursor_execute", self._count)

    def _count(self, conn, cursor, statement, *args):
        self.statements.append(statement)


# ------------------------------------------------------------ PUT /follow


def test_follow_user(client, seed, login, db):
    me, other = seed.users[0], seed.users[2]
    response = follow(client, other["id"], login(me["username"]))

    assert response.status_code == 204
    assert response.content == b""
    assert follow_rows(db, me["id"], other["id"]) == 1


def test_follow_twice_is_idempotent(client, seed, login, db):
    me, other = seed.users[0], seed.users[2]
    headers = login(me["username"])

    assert follow(client, other["id"], headers).status_code == 204
    assert follow(client, other["id"], headers).status_code == 204
    assert follow_rows(db, me["id"], other["id"]) == 1


def test_cannot_follow_yourself(client, seed, login, db):
    me = seed.users[0]
    response = follow(client, me["id"], login(me["username"]))

    assert response.status_code == 400
    assert follow_rows(db) == 0


def test_follow_unknown_user_is_404(client, seed, login, db):
    assert follow(client, 999999, login(seed.users[0]["username"])).status_code == 404
    assert follow_rows(db) == 0


def test_follow_requires_auth(client, seed):
    assert client.put(f"/users/{seed.users[1]['id']}/follow").status_code == 401


def test_follow_is_one_directional(client, seed, login):
    me, other = seed.users[0], seed.users[1]
    follow(client, other["id"], login(me["username"]))

    assert usernames(followers(client, other["id"])) == [me["username"]]
    assert usernames(following(client, me["id"])) == [other["username"]]
    # The other direction stays empty
    assert usernames(following(client, other["id"])) == []
    assert usernames(followers(client, me["id"])) == []


# --------------------------------------------------------- DELETE /follow


def test_unfollow(client, seed, login, db):
    me, other = seed.users[0], seed.users[2]
    headers = login(me["username"])
    follow(client, other["id"], headers)

    response = unfollow(client, other["id"], headers)
    assert response.status_code == 204
    assert follow_rows(db, me["id"], other["id"]) == 0


def test_unfollow_when_not_following_is_not_an_error(client, seed, login):
    headers = login(seed.users[0]["username"])
    other = seed.users[2]["id"]

    assert unfollow(client, other, headers).status_code == 204
    # And twice in a row after a real follow
    follow(client, other, headers)
    assert unfollow(client, other, headers).status_code == 204
    assert unfollow(client, other, headers).status_code == 204


def test_unfollow_only_removes_my_follow(client, seed, login):
    a, b, target = seed.users[0], seed.users[1], seed.users[2]
    follow(client, target["id"], login(a["username"]))
    follow(client, target["id"], login(b["username"]))

    unfollow(client, target["id"], login(a["username"]))
    assert usernames(followers(client, target["id"])) == [b["username"]]


def test_unfollow_unknown_user_is_404(client, seed, login):
    assert unfollow(client, 999999, login(seed.users[0]["username"])).status_code == 404


def test_unfollow_requires_auth(client, seed):
    assert client.delete(f"/users/{seed.users[2]['id']}/follow").status_code == 401


# ------------------------------------------- GET /followers and /following


def test_followers_most_recent_first(client, seed, login):
    target = seed.users[0]
    fans = seed.users[1:4]
    for fan in fans:
        follow(client, target["id"], login(fan["username"]))

    expected = [fan["username"] for fan in reversed(fans)]
    assert usernames(followers(client, target["id"])) == expected


def test_following_most_recent_first(client, seed, login):
    me = seed.users[0]
    headers = login(me["username"])
    idols = seed.users[1:4]
    for idol in idols:
        follow(client, idol["id"], headers)

    expected = [idol["username"] for idol in reversed(idols)]
    assert usernames(following(client, me["id"])) == expected


def test_example_from_the_exercise(client, seed, login):
    # Two users follow the target; the last one to follow comes first.
    target, first, last = seed.users[3], seed.users[1], seed.users[6]
    follow(client, target["id"], login(first["username"]))
    follow(client, target["id"], login(last["username"]))

    response = followers(client, target["id"], limit=2)
    assert response.json() == [
        {"id": last["id"], "username": last["username"]},
        {"id": first["id"], "username": first["username"]},
    ]


def test_refollowing_moves_you_to_the_top(client, seed, login):
    target, a, b = seed.users[0], seed.users[1], seed.users[2]
    follow(client, target["id"], login(a["username"]))
    follow(client, target["id"], login(b["username"]))
    # a unfollows and follows again: it is a new, more recent follow
    unfollow(client, target["id"], login(a["username"]))
    follow(client, target["id"], login(a["username"]))

    assert usernames(followers(client, target["id"])) == [a["username"], b["username"]]


def test_lists_never_expose_the_email(client, seed, login):
    a, b = seed.users[0], seed.users[1]
    follow(client, b["id"], login(a["username"]))

    for response in (followers(client, b["id"]), following(client, a["id"])):
        assert response.status_code == 200
        assert [set(u) for u in response.json()] == [{"id", "username"}]
        assert "@" not in response.text


def test_lists_are_public(client, seed, login):
    a, b = seed.users[0], seed.users[1]
    follow(client, b["id"], login(a["username"]))

    # No Authorization header at all
    assert followers(client, b["id"]).status_code == 200
    assert following(client, a["id"]).status_code == 200


def test_lists_of_user_without_follows_are_empty(client, seed):
    user_id = seed.users[5]["id"]
    assert usernames(followers(client, user_id)) == []
    assert usernames(following(client, user_id)) == []


def test_lists_unknown_user_is_404(client, seed):
    assert followers(client, 999999).status_code == 404
    assert following(client, 999999).status_code == 404


def test_lists_pagination(client, seed, login):
    target = seed.users[0]
    for fan in seed.users[1:6]:
        follow(client, target["id"], login(fan["username"]))

    everyone = usernames(followers(client, target["id"]))
    pages = [
        usernames(followers(client, target["id"], limit=2, offset=offset))
        for offset in (0, 2, 4, 6)
    ]
    assert [len(p) for p in pages] == [2, 2, 1, 0]
    assert pages[0] + pages[1] + pages[2] == everyone


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_lists_invalid_pagination(client, seed, params):
    user_id = seed.users[0]["id"]
    assert followers(client, user_id, **params).status_code == 422
    assert following(client, user_id, **params).status_code == 422


# ------------------------------------------------------- GET /users/{id}


def test_profile_counts_start_at_zero(client, seed):
    user = seed.users[0]
    assert client.get(f"/users/{user['id']}").json() == {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "followers_count": 0,
        "following_count": 0,
    }


def test_profile_counts(client, seed, login):
    target, a, b = seed.users[3], seed.users[1], seed.users[6]
    follow(client, target["id"], login(a["username"]))
    follow(client, target["id"], login(b["username"]))
    follow(client, b["id"], login(target["username"]))

    data = client.get(f"/users/{target['id']}").json()
    assert (data["followers_count"], data["following_count"]) == (2, 1)
    data = client.get(f"/users/{a['id']}").json()
    assert (data["followers_count"], data["following_count"]) == (0, 1)


def test_profile_counts_after_unfollow(client, seed, login):
    target, fan = seed.users[0], seed.users[1]
    follow(client, target["id"], login(fan["username"]))
    unfollow(client, target["id"], login(fan["username"]))

    data = client.get(f"/users/{target['id']}").json()
    assert data["followers_count"] == 0


def test_profile_is_a_single_query(client, seed, login):
    target = seed.users[0]
    for fan in seed.users[1:4]:
        follow(client, target["id"], login(fan["username"]))

    with QueryCounter() as q:
        data = client.get(f"/users/{target['id']}").json()

    assert data["followers_count"] == 3
    # The user and both counters come in the same SELECT (undefer_group)
    assert len(q.statements) == 1, q.statements


def test_other_user_endpoints_do_not_load_the_counters(client, seed, login):
    headers = login(seed.users[0]["username"])

    with QueryCounter() as q:
        users = client.get("/users/", headers=headers).json()

    assert len(users) == len(seed.users)
    assert "followers_count" not in users[0]
    # user lookup for the token + the list: not one extra query per user
    assert len(q.statements) == 2, q.statements


# ------------------------------------------------------ /home/following


@pytest.fixture
def social(seed, db):
    return seed_social(db, seed)


def authors(seed, n):
    """n seeded users that have written at least one post."""
    with_posts = [u for u in seed.users if seed.posts_by(u["id"])]
    assert len(with_posts) >= n, "the seed does not have enough authors"
    return with_posts[:n]


def expected_following_feed(seed, followed_ids):
    """Posts by the followed users, newest first. Seed posts are created one
    hour apart, so reversing the seed order sorts them by created_at desc."""
    return [p["id"] for p in reversed(seed.posts) if p["author_id"] in followed_ids]


def reader(seed, exclude):
    """A seeded user that is not in `exclude`, to read the feed."""
    excluded = {u["id"] for u in exclude}
    return next(u for u in seed.users if u["id"] not in excluded)


def test_following_feed_requires_auth(client, seed):
    assert client.get("/home/following").status_code == 401


def test_following_feed_empty_when_following_nobody(client, social, seed, login):
    # There are 20 posts, but I follow nobody: [] and no fallback
    response = client.get("/home/following", params=ALL, headers=login(seed.users[0]["username"]))
    assert post_ids(response) == []


def test_following_feed_empty_when_they_have_not_posted(client, social, seed, login):
    silent = next(u for u in seed.users if not seed.posts_by(u["id"]))
    me = reader(seed, [silent])
    headers = login(me["username"])
    follow(client, silent["id"], headers)

    assert post_ids(client.get("/home/following", params=ALL, headers=headers)) == []


def test_following_feed_shows_only_followed_authors_newest_first(client, social, seed, login):
    followed = authors(seed, 2)
    me = reader(seed, followed)
    headers = login(me["username"])
    for user in followed:
        follow(client, user["id"], headers)

    response = client.get("/home/following", params=ALL, headers=headers)
    expected = expected_following_feed(seed, {u["id"] for u in followed})
    assert expected, "the followed authors have no posts"
    assert post_ids(response) == expected
    assert {p["author_id"] for p in response.json()} <= {u["id"] for u in followed}


def test_following_feed_marks_likes_like_the_other_feeds(client, social, seed, login):
    followed = authors(seed, 3)
    me = reader(seed, followed)
    headers = login(me["username"])
    for user in followed:
        follow(client, user["id"], headers)

    mine = {l["post_id"] for l in social.likes if l["user_id"] == me["id"]}
    posts = client.get("/home/following", params=ALL, headers=headers).json()

    assert posts
    for p in posts:
        assert p["like_count"] == len(social.likes_on(p["id"]))
        assert p["liked_by_me"] == (p["id"] in mine)
        assert "my_rating" in p and "genres" in p


def test_unfollow_removes_their_posts_from_the_feed(client, social, seed, login):
    kept, dropped = authors(seed, 2)
    me = reader(seed, [kept, dropped])
    headers = login(me["username"])
    follow(client, kept["id"], headers)
    follow(client, dropped["id"], headers)

    unfollow(client, dropped["id"], headers)
    response = client.get("/home/following", params=ALL, headers=headers)
    assert post_ids(response) == expected_following_feed(seed, {kept["id"]})


def test_following_feed_pagination(client, social, seed, login):
    followed = authors(seed, 4)
    me = reader(seed, followed)
    headers = login(me["username"])
    for user in followed:
        follow(client, user["id"], headers)

    everything = post_ids(client.get("/home/following", params=ALL, headers=headers))
    assert len(everything) > 3
    first = post_ids(client.get("/home/following", params={"limit": 3}, headers=headers))
    rest = post_ids(client.get("/home/following", params={"limit": 100, "offset": 3}, headers=headers))
    assert first + rest == everything


def test_following_feed_for_every_seeded_user(client, social, seed, db, login):
    data = seed_follows(db, seed)
    for user in seed.users:
        response = client.get("/home/following", params=ALL, headers=login(user["username"]))
        expected = expected_following_feed(seed, set(data.following_of(user["id"])))
        assert post_ids(response) == expected, user["username"]


def test_following_feed_does_not_run_one_query_per_post(client, social, seed, login):
    followed = authors(seed, 4)
    me = reader(seed, followed)
    headers = login(me["username"])
    for user in followed:
        follow(client, user["id"], headers)

    with QueryCounter() as q:
        posts = client.get("/home/following", params=ALL, headers=headers).json()

    assert len(posts) > 3
    # user lookup + posts + genres + likes + ratings: a constant, not one per post
    assert len(q.statements) <= 6, q.statements


# ------------------------------------------------------------- database


def test_database_rejects_self_follow(seed, db):
    user_id = seed.users[0]["id"]
    db.add(Follow(follower_id=user_id, following_id=user_id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_database_rejects_duplicate_follow(seed, db):
    a, b = seed.users[0]["id"], seed.users[1]["id"]
    db.add(Follow(follower_id=a, following_id=b))
    db.commit()

    db.add(Follow(follower_id=a, following_id=b))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def new_user(client, name):
    """A fresh user with no posts, comments or likes (so it can be deleted)."""
    response = client.post(
        "/users/signup",
        json={"username": name, "email": f"{name}@test.com", "password": "secret"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_deleting_a_user_deletes_their_follows(client, seed, login, db):
    ghost = new_user(client, "ghost")
    a, b = seed.users[0], seed.users[1]
    follow(client, a["id"], login("ghost", "secret"))  # ghost -> a
    follow(client, ghost["id"], login(b["username"]))  # b -> ghost

    db.delete(db.get(User, ghost["id"]))
    db.commit()

    assert follow_rows(db, follower_id=ghost["id"]) == 0
    assert follow_rows(db, following_id=ghost["id"]) == 0
    assert client.get(f"/users/{a['id']}").json()["followers_count"] == 0
    assert client.get(f"/users/{b['id']}").json()["following_count"] == 0


def test_database_cascade_works_without_the_orm(client, seed, login, db):
    ghost = new_user(client, "ghost")
    follow(client, seed.users[0]["id"], login("ghost", "secret"))
    follow(client, ghost["id"], login(seed.users[1]["username"]))

    # A plain DELETE, as a script or another service would send it
    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": ghost["id"]})
    db.commit()

    assert follow_rows(db, follower_id=ghost["id"]) == 0
    assert follow_rows(db, following_id=ghost["id"]) == 0

"""
Tests for the /home feeds.

They use seed_social() (genres + likes on top of the normal seed) and compute
the expected result in plain Python from the seed data, then compare it with
what the API returns. If the SQL and the Python disagree, one of them is wrong.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest

from app.database.models.like import Like
from test.conf.seed import seed_social

ALL = {"limit": 100}  # every seeded post fits in one page


@pytest.fixture
def social(seed, db):
    return seed_social(db, seed)


def ids(response):
    assert response.status_code == 200, response.text
    return [p["id"] for p in response.json()]


def position(seed):
    """post_id -> creation order (seed posts are created one hour apart)."""
    return {p["id"]: i for i, p in enumerate(seed.posts)}


# ------------------------------------------------ expected results, in Python


def expected_latest(seed):
    return [p["id"] for p in reversed(seed.posts)]


def expected_popular(seed, social, exclude_author=None, extra_likes=None):
    counts = Counter(l["post_id"] for l in social.likes)
    counts.update(extra_likes or {})
    pos = position(seed)
    posts = [p["id"] for p in seed.posts if p["author_id"] != exclude_author]
    return sorted(posts, key=lambda pid: (-counts[pid], -pos[pid]))


def expected_recommended(seed, social, user_id):
    mine = set(social.user_genres[user_id])
    pos = position(seed)
    shared = {
        p["id"]: len(mine & set(social.post_genres[p["id"]]))
        for p in seed.posts
        if p["author_id"] != user_id
    }
    posts = [pid for pid, n in shared.items() if n > 0]
    return sorted(posts, key=lambda pid: (-shared[pid], -pos[pid]))


def expected_discover(seed, social, user_id):
    mine = set(social.user_genres[user_id])
    pos = position(seed)
    posts = [
        p["id"]
        for p in seed.posts
        if p["author_id"] != user_id and set(social.post_genres[p["id"]]) - mine
    ]

    def is_bridge(pid):
        return bool(mine & set(social.post_genres[pid]))

    return sorted(posts, key=lambda pid: (-is_bridge(pid), -pos[pid]))


def user_with_most_recommendations(seed, social):
    """The seeded user with genres whose recommended feed is the longest, so
    the tests are not checking an empty list."""
    candidates = [u for u in seed.users if social.user_genres[u["id"]]]
    user = max(candidates, key=lambda u: len(expected_recommended(seed, social, u["id"])))
    assert expected_recommended(seed, social, user["id"]), "seed gives no recommendations"
    return user


def user_without_genres(seed, social):
    return next(u for u in seed.users if not social.user_genres[u["id"]])


# ------------------------------------------------------------------ latest


def test_latest(client, social, seed):
    assert ids(client.get("/home/latest", params=ALL)) == expected_latest(seed)


def test_latest_is_public(client, social):
    assert client.get("/home/latest").status_code == 200


# ----------------------------------------------------------------- popular


def test_popular(client, social, seed):
    assert ids(client.get("/home/popular", params=ALL)) == expected_popular(seed, social)


def test_popular_only_counts_recent_likes(client, social, seed, db):
    # An old like on the post that is currently last in the ranking
    last = expected_popular(seed, social)[-1]
    author = next(p["author_id"] for p in seed.posts if p["id"] == last)
    liker = next(
        u["id"] for u in seed.users
        if u["id"] != author and {"user_id": u["id"], "post_id": last} not in social.likes
    )
    db.add(Like(user_id=liker, post_id=last,
                created_at=datetime.now(timezone.utc) - timedelta(days=30)))
    db.commit()

    # Last 7 days: the old like does not count
    week = ids(client.get("/home/popular", params={**ALL, "days": 7}))
    assert week == expected_popular(seed, social)
    # Last 60 days: it does
    two_months = ids(client.get("/home/popular", params={**ALL, "days": 60}))
    assert two_months == expected_popular(seed, social, extra_likes={last: 1})


def test_popular_is_public(client, social):
    assert client.get("/home/popular").status_code == 200


# ------------------------------------------------------------- recommended


def test_recommended(client, social, seed, login):
    user = user_with_most_recommendations(seed, social)
    response = client.get("/home/recommended", params=ALL, headers=login(user["username"]))
    assert ids(response) == expected_recommended(seed, social, user["id"])


def test_recommended_shares_a_genre_and_excludes_mine(client, social, seed, login):
    user = user_with_most_recommendations(seed, social)
    mine = set(social.user_genres[user["id"]])
    posts = client.get("/home/recommended", params=ALL, headers=login(user["username"])).json()

    assert all(p["author_id"] != user["id"] for p in posts)
    assert all(mine & {g["name"] for g in p["genres"]} for p in posts)


def test_recommended_without_genres_falls_back_to_popular(client, social, seed, login):
    user = user_without_genres(seed, social)
    response = client.get("/home/recommended", params=ALL, headers=login(user["username"]))
    assert ids(response) == expected_popular(seed, social, exclude_author=user["id"])


def test_recommended_marks_my_likes(client, social, seed, login):
    user = user_with_most_recommendations(seed, social)
    mine = {l["post_id"] for l in social.likes if l["user_id"] == user["id"]}
    posts = client.get("/home/recommended", params=ALL, headers=login(user["username"])).json()
    assert all(p["liked_by_me"] == (p["id"] in mine) for p in posts)


def test_recommended_requires_auth(client, social):
    assert client.get("/home/recommended").status_code == 401


# ---------------------------------------------------------------- discover


def test_discover(client, social, seed, login):
    user = user_with_most_recommendations(seed, social)
    response = client.get("/home/discover", params=ALL, headers=login(user["username"]))
    assert ids(response) == expected_discover(seed, social, user["id"])


def test_discover_bridges_first(client, social, seed, login):
    user = user_with_most_recommendations(seed, social)
    mine = set(social.user_genres[user["id"]])
    posts = client.get("/home/discover", params=ALL, headers=login(user["username"])).json()

    bridge_flags = [bool(mine & {g["name"] for g in p["genres"]}) for p in posts]
    # All the True values come before all the False values
    assert bridge_flags == sorted(bridge_flags, reverse=True)
    # And every post brings at least one genre the user does not follow
    assert all({g["name"] for g in p["genres"]} - mine for p in posts)


def test_discover_without_genres_shows_everything_but_mine(client, social, seed, login):
    user = user_without_genres(seed, social)
    response = client.get("/home/discover", params=ALL, headers=login(user["username"]))
    assert ids(response) == expected_discover(seed, social, user["id"])


def test_discover_requires_auth(client, social):
    assert client.get("/home/discover").status_code == 401


# -------------------------------------------------------------- pagination


def test_pagination_pages_join_up(client, social):
    first = ids(client.get("/home/latest", params={"limit": 5, "offset": 0}))
    second = ids(client.get("/home/latest", params={"limit": 5, "offset": 5}))
    both = ids(client.get("/home/latest", params={"limit": 10, "offset": 0}))
    assert len(first) == 5
    assert first + second == both


def test_default_page_size(client, social):
    assert len(ids(client.get("/home/latest"))) == 20


def test_offset_past_the_end_is_empty(client, social):
    assert ids(client.get("/home/latest", params={"offset": 1000})) == []


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"days": 0}],
)
def test_invalid_pagination(client, social, params):
    assert client.get("/home/popular", params=params).status_code == 422

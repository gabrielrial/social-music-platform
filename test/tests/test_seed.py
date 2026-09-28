from app.database.models.like import Like
from test.conf.seed import seed_social


def test_seed_social(seed, db):
    data = seed_social(db, seed)

    # Every post has at least one genre
    assert all(1 <= len(g) <= 3 for g in data.post_genres.values())
    assert len(data.post_genres) == len(seed.posts)

    # Every user has genres except the last one
    last = seed.users[-1]["id"]
    assert data.user_genres[last] == []
    assert all(2 <= len(g) <= 4 for uid, g in data.user_genres.items() if uid != last)

    # Some likes, none on your own post, and the database has them all
    authors = {p["id"]: p["author_id"] for p in seed.posts}
    assert data.likes
    assert all(authors[l["post_id"]] != l["user_id"] for l in data.likes)
    assert db.query(Like).count() == len(data.likes)


def test_seed_social_shows_up_in_the_api(client, seed, db, login):
    data = seed_social(db, seed)
    post = seed.posts[0]

    response = client.get(f"/posts/{post['id']}").json()
    assert [g["name"] for g in response["genres"]] == data.post_genres[post["id"]]
    assert response["like_count"] == len(data.likes_on(post["id"]))

    user = seed.users[0]
    genres = client.get("/users/me/genres", headers=login(user["username"])).json()
    assert [g["name"] for g in genres] == data.user_genres[user["id"]]


def test_seed_follows(seed, db):
    from app.database.models.follow import Follow
    from test.conf.seed import seed_follows

    data = seed_follows(db, seed)

    # Some follows, never yourself, and the first user follows nobody
    assert data.follows
    assert all(f["follower_id"] != f["following_id"] for f in data.follows)
    assert data.following_of(seed.users[0]["id"]) == []
    assert db.query(Follow).count() == len(data.follows)


def test_seed_ratings(seed, db):
    from app.database.models.rating import Rating
    from test.conf.seed import seed_ratings

    data = seed_ratings(db, seed)

    # Some ratings, all between 1 and 5, never on your own post
    authors = {p["id"]: p["author_id"] for p in seed.posts}
    assert data.ratings
    assert all(1 <= r["score"] <= 5 for r in data.ratings)
    assert all(authors[r["post_id"]] != r["user_id"] for r in data.ratings)
    assert db.query(Rating).count() == len(data.ratings)


def test_seed_ratings_show_up_in_the_api(client, seed, db):
    from decimal import ROUND_HALF_UP, Decimal

    from test.conf.seed import seed_ratings

    data = seed_ratings(db, seed)
    for post in seed.posts:
        scores = [r["score"] for r in data.ratings_on(post["id"])]
        response = client.get(f"/posts/{post['id']}").json()
        assert response["rating_count"] == len(scores)
        # Postgres rounds halves away from zero (3.25 -> 3.3); Python's
        # round() would give 3.2, so compute it the same way Postgres does.
        expected = (
            float((Decimal(sum(scores)) / len(scores)).quantize(Decimal("0.1"), ROUND_HALF_UP))
            if scores else None
        )
        assert response["rating_avg"] == expected


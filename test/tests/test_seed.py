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

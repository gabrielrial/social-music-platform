# 🧪 Tests — Rate API

API test suite built with **pytest** and FastAPI's `TestClient`. The tests do not start a server: they talk to the application directly.

---

## 📁 Structure

```
test/
├── conftest.py              # Shared fixtures + database override
├── conf/
│   ├── conf_database.py     # Engine, sessions and create/drop of the test database
│   └── seed.py              # Seed data (10 users, 20 posts, 60 comments) + seed_social() (genres, likes) + seed_follows()
└── tests/
    ├── test_basic.py        # Smoke tests
    ├── test_users.py        # Signup, login, /me, listing
    ├── test_posts.py        # Post CRUD, permissions and post genres
    ├── test_comments.py     # Comments
    ├── test_genres.py       # Genre catalog
    ├── test_user_genres.py  # GET/PUT /users/me/genres
    ├── test_likes.py        # Like/unlike, like_count, liked_by_me
    ├── test_ratings.py      # PUT/DELETE /posts/{id}/rating, rating_avg, my_rating
    ├── test_follow.py       # Follow/unfollow, followers/following lists, counters, /home/following
    ├── test_seed.py         # seed_social() and seed_follows() themselves
    └── test_home.py         # The /home feeds based on genres and likes, and pagination
```

`conftest.py` must live in `test/`, not inside `conf/`: pytest loads it automatically by name, and its fixtures only reach the tests in its own folder and subfolders.

Every folder needs an `__init__.py`. That is what makes pytest add the project root to `sys.path`, so `import app...` works from the tests.

---

## ▶️ Running the tests

With the `db_test` container running (`docker compose up -d db_test`), from the project root:

```bash
pytest -v                                               # everything
pytest test/tests/test_posts.py -v                      # one file
pytest test/tests/test_posts.py::test_delete_own_post   # one test
pytest -x                                               # stop at the first failure
pytest -s                                               # show print() output
```

---

## 🗄️ The test database

The tests **never touch the development database**. It works with three pieces:

1. `conf/conf_database.py` creates its own engine from `TEST_DATABASE_URL` (default `forumdb_test` on port **5433**). It never reads `DATABASE_URL`, and it refuses to start if both point to the same database.
2. `conftest.py` sets `app.dependency_overrides[get_db] = override_get_db`: wherever an endpoint asks for `Depends(get_db)`, FastAPI hands it a test database session instead. The endpoints do not change.
3. The `setup_db` fixture (`autouse=True`) creates the tables before each test and drops them afterwards.

As a result, **every test starts with an empty database**. No test can depend on what another test did.

---

## 🔌 Available fixtures

| Fixture    | What it provides                                                        |
|------------|-------------------------------------------------------------------------|
| `client`   | A `TestClient` for the app, to make simulated HTTP requests             |
| `seed`     | Fills the database with seed data and returns a `SeedData` object       |
| `login`    | A `login(username, password)` function that returns the `Authorization` header |
| `db`       | A direct session to the test database, to check things the API does not expose |
| `setup_db` | Creates and drops the tables. `autouse`: applied automatically          |

A fixture is requested by adding it as a test **parameter**; it is never imported:

```python
def test_create_post(client, seed, login):
    headers = login(seed.users[0]["username"])
    response = client.post("/posts/", json={...}, headers=headers)
    assert response.status_code == 201
```

---

## 🌱 Seed data (`conf/seed.py`)

The `seed` fixture loads:

- **10 users** (`john0`, `janis1`, `muddy2`…), all with the password `password123` (`SEED_PASSWORD`)
- **20 posts** with a random author; the title is a blues/rock album or song depending on `post_type`
- **3 comments per post** (60 in total) with a random author

Important details:

- It uses `random.Random(42)`: the data looks random but is **identical on every run**, so a failure can be reproduced.
- The password is hashed **only once**, when the module is imported: bcrypt is slow by design, and hashing in every test would make the suite very slow.
- Every post and comment gets its own `created_at`, so ordering by date is predictable.
- `seed` is **not** `autouse`: only the tests that ask for it load data.

`SeedData` has helpers to avoid repeating filters: `posts_by(user_id)`, `comments_by(user_id)`, `comments_on(post_id)` and `likes_on(post_id)`.

The genre catalog is **not** part of the seed: `setup_test_db()` loads it before every test, like the app does on startup, so `GET /genres/` always has data.

### `seed_social()`: genres and likes

`seed_social(db, seed)` adds, on top of the normal seed: 1–3 genres per post, 2–4 favourite genres per user (except the **last user, who has none**, to test fallbacks) and random likes (30%, never on your own post). It fills `user_genres`, `post_genres` and `likes` in `SeedData`.

It is a separate function on purpose: most tests want the plain seed so their expected numbers stay simple. `test_home.py` uses it through a `social` fixture, and `make seed` uses it for the development database.

### `seed_follows()`: who follows whom

`seed_follows(db, seed)` makes every user follow each other user with a 30% chance, **except the first user (`john0`), who follows nobody** (to show the empty "Following" feed). It fills `SeedData.follows` and adds the helper `following_of(user_id)`. Each follow gets its own `created_at`, so the lists have a predictable order.

It is separate from `seed_social()` because both use a fixed random generator: generating follows there would consume its random numbers and change the likes that `test_home.py` expects.

`test_home.py` computes the expected feed **in plain Python** from `SeedData` and compares it with the API response: if the SQL and the Python disagree, one of them is wrong. `test_follow.py` does the same for `/home/following`.

---

## 👥 `test_follow.py` (exercise 4)

| Group | What it checks |
|---|---|
| `PUT /follow` | 204 with an empty body; twice → still one row; yourself → 400 and no row; unknown user → 404; no token → 401; following is one-directional |
| `DELETE /follow` | 204; not following / twice → 204; only removes my follow; unknown user → 404; no token → 401 |
| `/followers`, `/following` | Most recent follow first (the example from the exercise, and re-following moves you to the top); only `id` and `username`, never the email; public; empty lists; unknown user → 404; pagination pages join up; invalid `limit`/`offset` → 422 |
| `GET /users/{id}` | `followers_count` / `following_count` start at 0, add up, go down after unfollowing; the user and both counters come in **one** SQL query; `GET /users/` does not load the counters |
| `/home/following` | 401 without a token; `[]` when following nobody or when they have not posted; only followed authors, newest first; `like_count` / `liked_by_me` like the other feeds; unfollowing removes their posts; pagination; the expected feed of **every** seeded user with `seed_follows()`; a constant number of queries |
| Database | The `CHECK` rejects a self-follow and the primary key a duplicate (`IntegrityError`); deleting a user deletes their follows in both directions, through the ORM and with a plain SQL `DELETE` |

The query-count tests use a small `QueryCounter` context manager that listens to SQLAlchemy's `before_cursor_execute` event on the test engine.

---

## 🐛 Tests marked `xfail`

```python
@pytest.mark.xfail(reason="BUG: ...", strict=True)
```

Marks a test that fails because of a **known bug**: it shows up as `XFAIL` and does not break the suite. With `strict=True`, once the bug is fixed the test passes and pytest reports `XPASS(strict)`, which is the signal to remove the mark.

There are none right now. The last one covered `GET /comment/me` returning 404 instead of `[]`; once it was fixed the mark was removed.

---

## 📝 Pending tests

- **`GET /comment/user/{user_id}`** (endpoint added recently, not covered yet). Add to `test_comments.py`:
  1. User with comments → 200, count matches `seed.comments_by(user["id"])` and every item has that `author_id`.
  2. User without comments → 200 and `[]`. Sign up a new user inside the test and take its `id` from the response.
  3. Unknown user (e.g. `999999`) → 404.
  4. Optional: results are ordered by `created_at`.

  The endpoint is public, so none of these need the `login` fixture.

---

## ✍️ Conventions for new tests

- Files are named `test_*.py` and functions `test_*`; otherwise pytest will not find them.
- One test, one thing. The name should say what it checks (`test_update_other_users_post_forbidden`).
- Every test must work **on its own and in any order**. If it needs data, a fixture provides it.
- Cover the failure cases too: 401 without a token, 403 for another user's resource, 404 if it does not exist, 422 if the body is invalid.
- `/users/login` is sent with `data=` (it is a form). Every other endpoint uses `json=`.

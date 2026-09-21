# 🎵 Rate API — Social Music Backend

Backend for a social music platform: users sign up, authenticate, and publish posts about albums and songs that other users can comment on and like. Posts and users have music genres, which power a personalised home feed. Built with **FastAPI** and **PostgreSQL**.

---

## 🧱 Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL 17
- **ORM:** SQLAlchemy 2.0
- **Authentication:** JWT (`python-jose`)
- **Password hashing:** Passlib + bcrypt
- **Tests:** pytest + FastAPI `TestClient`
- **Containers:** Docker Compose (development and test databases)

---

## 📁 Project structure

```
app/
├── main.py                   # Entry point (FastAPI app + lifespan)
├── api/routes/               # Endpoints (users, posts, comments, genres, home)
├── services/                 # Business logic (auth, users, genres, likes, feed)
├── utils/security.py         # Password hashing and JWT config
└── database/
    ├── conf/                 # SQLAlchemy connection and get_db dependency
    ├── models/               # ORM models (user, post, comment, genre, like)
    └── schema/               # Pydantic schemas (request/response)

scripts/seed_dev.py           # Fills the dev database with sample data (make seed)

test/                         # Test suite (see test/README.md)
├── conftest.py               # Shared fixtures
├── conf/                     # Test database config and seed data
└── tests/                    # The tests

docker/
└── docker-compose.yml        # Development (5432) and test (5433) Postgres

requirements.txt              # Python dependencies (app + tests)
```

---

## ⚙️ Prerequisites

- Python 3.10+
- Docker and Docker Compose
- `pip`

---

## 🚀 Getting started

### Quick start (Makefile)

```bash
git clone <repo-url>
cd Rate
make install   # create .venv and install dependencies
make run       # start the dev database and the API
```

| Command        | What it does                                              |
|----------------|-----------------------------------------------------------|
| `make help`    | List all commands                                         |
| `make install` | Create `.venv` and install `requirements.txt`             |
| `make run`     | Start the dev database (`db`) and the API with `--reload` |
| `make seed`    | Fill the dev database with sample users, posts, comments, genres and likes (only if it has no users) |
| `make seed-reset` | Wipe the dev database tables and seed them again (asks for confirmation) |
| `make test`    | Start the test database (`db_test`) and run `pytest -v`   |
| `make down`    | Stop the containers (development data is kept)            |
| `make db-drop` | Stop the containers and **delete** the development data (asks for confirmation) |
| `make clean`   | Remove `__pycache__` and `.pytest_cache`                  |

The steps below explain what those commands do, if you prefer to run them by hand.

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # includes pytest and httpx for the tests
```

### 2. Start the databases

```bash
cd docker
docker compose up -d
```

This starts two containers:

| Service   | Database       | Local port | Data                               |
|-----------|----------------|------------|------------------------------------|
| `db`      | `forumdb`      | `5432`     | Persistent (Docker volume)         |
| `db_test` | `forumdb_test` | `5433`     | In RAM, wiped when the container stops |

Both use user `admin` and password `password`.

> The left-hand port is the one on your machine; inside each container Postgres always listens on 5432.

### 3. Run the API

From the project root:

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Tables are created when the server starts (`create_all` inside FastAPI's `lifespan`), so there are no migrations to run. The genre catalog is loaded at the same time.

To have something to look at in `/docs`, run `make seed`: 10 users (`john0`, `janis1`… `jimi9`), all with password `password123`, 20 posts, 60 comments, genres and likes. `jimi9` has no favourite genres on purpose, to show the fallback of `/home/recommended`.

> ⚠️ `python app/main.py` **does not work**: Python cannot find the `app` package that way. Use `uvicorn app.main:app` or `python -m app.main` from the project root.

---

## 🔧 Configuration

The application reads these environment variables:

| Variable       | Default                                              | Description                 |
|----------------|------------------------------------------------------|-----------------------------|
| `DATABASE_URL` | `postgresql://admin:password@localhost:5432/forumdb` | PostgreSQL connection       |
| `JWT_SECRET`   | `dev-secret-not-for-production`                      | Key used to sign the tokens |
| `CORS_ORIGINS` | `http://localhost:8080`                              | Comma-separated origins allowed to call the API from a browser |
| `TEST_DATABASE_URL` | `postgresql://admin:password@localhost:5433/forumdb_test` | Database used by the tests (never `DATABASE_URL`) |

Both must be set in production: the `JWT_SECRET` default is for development only.

---

## 📡 Endpoints

### Users (`/users`)

| Method | Route            | Description                  | Auth |
|--------|------------------|------------------------------|------|
| POST   | `/users/signup`  | Register a new user          | No   |
| POST   | `/users/login`   | Log in, returns a JWT        | No   |
| GET    | `/users/me`      | Current authenticated user   | Yes  |
| GET    | `/users/{id}`    | Get a user by ID             | No   |
| GET    | `/users/`        | List all users               | Yes  |
| GET    | `/users/me/genres` | The current user's favourite genres | Yes |
| PUT    | `/users/me/genres` | Replace them: `{"genre_ids": [1, 4]}` (`[]` clears them) | Yes |

### Posts (`/posts`)

| Method | Route             | Description                         | Auth |
|--------|-------------------|-------------------------------------|------|
| GET    | `/posts/`         | List posts (newest first)           | No   |
| GET    | `/posts/me`       | Posts by the authenticated user     | Yes  |
| GET    | `/posts/{id}`     | Get a post by ID                    | No   |
| POST   | `/posts/`         | Create a post                       | Yes  |
| PATCH  | `/posts/{id}`     | Update a post (author only)         | Yes  |
| DELETE | `/posts/{id}`     | Delete a post (author only)         | Yes  |
| POST   | `/posts/{id}/like` | Like a post (idempotent)           | Yes  |
| DELETE | `/posts/{id}/like` | Remove your like (idempotent)      | Yes  |

A post has a `title`, `content`, `post_type` (`album` or `song`) and optional `genre_ids` (unknown ids give 422). Responses include its `genres`, `like_count` and `liked_by_me`. The public endpoints accept a token too: with one, `liked_by_me` is filled in for that user; without one it is always `false`; with an invalid or expired one they return 401. Deleting a post also deletes its comments, likes and genre links (cascade). Liking twice keeps a single like: the `likes` table has the primary key `(user_id, post_id)`.

### Genres (`/genres`)

| Method | Route      | Description                  | Auth |
|--------|------------|------------------------------|------|
| GET    | `/genres/` | Genre catalog, sorted by name | No  |

The catalog lives in `GENRE_CATALOG` (`app/services/genres.py`) and is inserted on startup; adding a genre there is enough.

### Home feeds (`/home`)

| Method | Route               | Description                                                              | Auth |
|--------|---------------------|--------------------------------------------------------------------------|------|
| GET    | `/home/latest`      | Newest posts first                                                       | No   |
| GET    | `/home/popular`     | Most likes in the last `days` days (default 7); posts without recent likes go last | No |
| GET    | `/home/recommended` | Posts sharing at least one genre with you, most shared genres first. Falls back to `popular` if you have no genres | Yes |
| GET    | `/home/discover`    | Posts with at least one genre you do not follow; "bridge" posts (that also share one of yours) first | Yes |

All feeds are paginated with `?limit=` (1–100, default 20) and `?offset=` (default 0). `recommended` and `discover` never show your own posts. The queries are in `app/services/feed.py`.

### Comments (`/comment`)

| Method | Route                      | Description                          | Auth |
|--------|----------------------------|--------------------------------------|------|
| GET    | `/comment/`                | List all comments                    | No   |
| GET    | `/comment/me`              | Comments by the authenticated user   | Yes  |
| GET    | `/comment/user/{user_id}`  | Comments by a given user             | No   |
| GET    | `/comment/{id}`            | Get a comment by ID                  | No   |
| POST   | `/comment/post/{post_id}`  | Comment on a post                    | Yes  |

`GET /comment/user/{user_id}` returns 404 if the user does not exist, and an empty list if the user exists but has not commented yet.

---

## 🔐 Authentication

1. Sign up with `POST /users/signup` (the password is stored hashed with bcrypt).
2. Log in with `POST /users/login`. It is sent as a **form** (`OAuth2PasswordRequestForm`: `username` and `password` fields), not as JSON.
3. Send the token on protected routes: `Authorization: Bearer <token>`.
4. The token expires after **15 minutes** (`ACCESS_TOKEN_DURATION` in `app/utils/security.py`).

---

## 🧪 Tests

```bash
make test      # or, with the db_test container already running: pytest -v
```

The tests run against the test Postgres (`db_test`, port 5433) and create and drop the tables around every test, so they never touch your development data. The `db` container is not even needed to run them.

Details (fixtures, seed data, how to add a test) are in **[test/README.md](test/README.md)**.

---

## 🗺️ Next steps

### Missing tests

- **`GET /comment/user/{user_id}` has no tests yet.** Cases to cover, in `test/tests/test_comments.py`:
  1. User with comments → 200, only that user's comments (`seed.comments_by(user_id)` gives the expected list).
  2. User without comments → 200 and `[]` (sign up a new user inside the test).
  3. Unknown user → 404.
  4. Optional: results are ordered by `created_at`.

### Inconsistencies

- `GET /comment/user/{user_id}` orders comments oldest first, while the other list endpoints return newest first (`.desc()`).
- `PATCH /posts/{id}` behaves like a PUT: it requires `title`, `content` and `post_type`. A real PATCH would use a `PostUpdate` schema with optional fields.

### Home feature (`feature/home`)

- `GET /home/latest` duplicates `GET /posts/` with pagination: decide whether to keep both or paginate `/posts/` and drop `latest`.
- `passlib` is unmaintained and logs a `(trapped) error reading bcrypt version` traceback with bcrypt ≥ 4.1 (harmless). Replace it with `bcrypt` directly.
- Posts can be created without genres; they never appear in `recommended`/`discover`.

### Improvements

- `GET /posts/{post_id}/comments`, and edit/delete for comments.
- Input validation: `EmailStr`, minimum password length, non-empty titles and comments.
- `POST /users/signup` should return `201 Created`.
- Split test dependencies into a `requirements-dev.txt`.
- Alembic for migrations (`create_all` does not update existing tables).
- Pagination on the remaining list endpoints (`/posts/`, `/comment/`), and indexes on the foreign keys.
- A Dockerfile for the API, added to `docker-compose.yml`.
- Ideas: a `rating` on posts, replies to comments, `updated_at` on posts.

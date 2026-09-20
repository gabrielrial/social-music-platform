"""
Test data ("seed") for the test suite.

seed_database() fills the test database with:
  - 10 users
  - 20 posts (random author, random album or song)
  - 3 comments per post (60 in total, random author)

It uses random.Random(42): the data looks random but is ALWAYS the same on
every run, so a failing test fails the same way next time and can be
investigated.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.database.models.comment import Comment
from app.database.models.post import Post, PostType
from app.database.models.user import User
from app.utils.security import hash_password

N_USERS = 10
N_POSTS = 20
COMMENTS_PER_POST = 3

# Every seeded user shares the same password, so any of them can log in
# from a test.
SEED_PASSWORD = "password123"

# bcrypt is slow by design (~0.2 s per hash). Hash once at import time and
# reuse it, instead of hashing 10 times in every single test.
_SEED_PASSWORD_HASH = hash_password(SEED_PASSWORD)

_NAMES = ["john", "janis", "muddy", "stevie", "bonnie",
          "howlin", "robert", "etta", "keith", "jimi"]

_ALBUMS = [
    "The Dark Side of the Moon",
    "Led Zeppelin IV",
    "Electric Ladyland",
    "Exile on Main St.",
    "Texas Flood",
    "Born to Run",
    "Rumours",
    "Let It Bleed",
    "Blues Breakers with Eric Clapton",
    "Layla and Other Assorted Love Songs",
    "Who's Next",
    "Moanin' in the Moonlight",
]

_SONGS = [
    "Cross Road Blues",
    "Hoochie Coochie Man",
    "Stormy Monday",
    "Whole Lotta Love",
    "Sweet Home Chicago",
    "Pride and Joy",
    "Born Under a Bad Sign",
    "Black Dog",
    "Gimme Shelter",
    "The Thrill Is Gone",
]

_REVIEWS = [
    "A masterpiece from start to finish.",
    "Flawless production, but it lacks soul.",
    "I cannot stop listening to this one.",
    "Much better live than in the studio.",
    "The second half drops off quite a bit.",
    "Raw, honest songwriting. It got to me.",
]

_COMMENTS = [
    "Could not agree more.",
    "Best thing I have heard all year.",
    "Honestly, I do not rate it that highly.",
    "Have you listened to it on vinyl?",
    "Adding it to my list.",
    "The third track is the highlight.",
]

# Fixed base date. Every post and comment gets its own timestamp so that
# ordering by created_at is predictable (otherwise Postgres would give them
# all the same transaction timestamp).
_BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class SeedData:
    """What seed_database() returns: plain dicts instead of ORM objects, so
    the data can still be read after the session is closed."""

    password: str
    users: list[dict] = field(default_factory=list)     # {id, username, email}
    posts: list[dict] = field(default_factory=list)     # {id, author_id, title, post_type}
    comments: list[dict] = field(default_factory=list)  # {id, author_id, post_id, content}

    def posts_by(self, user_id: int) -> list[dict]:
        return [p for p in self.posts if p["author_id"] == user_id]

    def comments_by(self, user_id: int) -> list[dict]:
        return [c for c in self.comments if c["author_id"] == user_id]

    def comments_on(self, post_id: int) -> list[dict]:
        return [c for c in self.comments if c["post_id"] == post_id]


def seed_database(db: Session, rng_seed: int = 42) -> SeedData:
    rng = random.Random(rng_seed)
    data = SeedData(password=SEED_PASSWORD)

    # --- Users ----------------------------------------------------------
    users = [
        User(
            username=f"{name}{i}",
            email=f"{name}{i}@test.com",
            password_hash=_SEED_PASSWORD_HASH,
        )
        for i, name in enumerate(_NAMES[:N_USERS])
    ]
    db.add_all(users)
    db.flush()  # sends the INSERTs without committing -> ids are available

    # --- Posts ----------------------------------------------------------
    posts = []
    for i in range(N_POSTS):
        post_type = rng.choice(list(PostType))
        title = rng.choice(_ALBUMS if post_type is PostType.ALBUM else _SONGS)
        posts.append(
            Post(
                title=title,
                content=rng.choice(_REVIEWS),
                post_type=post_type,
                author_id=rng.choice(users).id,
                created_at=_BASE_TIME + timedelta(hours=i),
            )
        )
    db.add_all(posts)
    db.flush()

    # --- Comments -------------------------------------------------------
    comments = []
    for post in posts:
        for j in range(COMMENTS_PER_POST):
            comments.append(
                Comment(
                    content=rng.choice(_COMMENTS),
                    author_id=rng.choice(users).id,
                    post_id=post.id,
                    created_at=post.created_at + timedelta(minutes=10 * (j + 1)),
                )
            )
    db.add_all(comments)
    db.commit()

    # Copy everything into plain dicts before the session goes away.
    data.users = [{"id": u.id, "username": u.username, "email": u.email} for u in users]
    data.posts = [
        {"id": p.id, "author_id": p.author_id, "title": p.title, "post_type": p.post_type.value}
        for p in posts
    ]
    data.comments = [
        {"id": c.id, "author_id": c.author_id, "post_id": c.post_id, "content": c.content}
        for c in comments
    ]
    return data

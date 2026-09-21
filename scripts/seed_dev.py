"""
Fill the DEVELOPMENT database (DATABASE_URL, forumdb on port 5432) with the
same sample data the tests use, plus genres and likes, so the API has
something to show in /docs without creating everything by hand.

    make seed         # only if the database has no users yet
    make seed-reset   # wipe every table and seed again (asks first)

Every user has the password `password123`.
"""

import sys

from app.database.conf.alch_conf import Base, SessionLocal, engine
from app.database.models import comment, genre, like, post, user  # noqa: F401 (registers the tables)
from app.database.models.user import User
from app.services.genres import seed_genres
from test.conf.seed import SEED_PASSWORD, seed_database, seed_social


def main(reset: bool) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_genres(db)

        if db.query(User).first() is not None:
            sys.exit(
                "The development database already has users: nothing was changed.\n"
                "Run `make seed-reset` to wipe it and seed it again."
            )

        data = seed_database(db)
        seed_social(db, data)

    print(f"Seeded {engine.url.render_as_string(hide_password=True)}")
    print(f"  {len(data.users)} users, {len(data.posts)} posts, "
          f"{len(data.comments)} comments, {len(data.likes)} likes")
    print(f"  Log in as any of them with password '{SEED_PASSWORD}':")
    for u in data.users:
        genres = ", ".join(data.user_genres[u["id"]]) or "(no genres)"
        print(f"    {u['username']:<10} likes {genres}")


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)

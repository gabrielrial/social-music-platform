from sqlalchemy.orm import Session
from app.database.models.genre import Genre

# Genres every database starts with. To add one, append it here: the next
# startup inserts it (existing rows are left alone).
GENRE_CATALOG = [
    "blues",
    "classical",
    "country",
    "electronic",
    "folk",
    "funk",
    "hip-hop",
    "jazz",
    "metal",
    "pop",
    "punk",
    "r&b",
    "reggae",
    "rock",
    "soul",
]


def seed_genres(db: Session) -> None:
    """Insert the catalog genres that are missing. Safe to run on every
    startup: running it twice does not create duplicates."""
    existing = {name for (name,) in db.query(Genre.name).all()}
    missing = [Genre(name=name) for name in GENRE_CATALOG if name not in existing]
    if missing:
        db.add_all(missing)
        db.commit()

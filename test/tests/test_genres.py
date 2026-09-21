import pytest
from sqlalchemy.exc import IntegrityError

from app.database.models.genre import Genre
from app.services.genres import GENRE_CATALOG, seed_genres


def test_list_genres(client):
    response = client.get("/genres/")
    assert response.status_code == 200
    names = [g["name"] for g in response.json()]
    assert set(names) == set(GENRE_CATALOG)


def test_list_genres_sorted_by_name(client):
    names = [g["name"] for g in client.get("/genres/").json()]
    assert names == sorted(names)


def test_list_genres_no_auth_needed(client):
    # No Authorization header: the catalog is public.
    assert client.get("/genres/").status_code == 200


def test_seed_genres_is_idempotent(db):
    seed_genres(db)  # setup_db already ran it once
    assert db.query(Genre).count() == len(GENRE_CATALOG)


def test_genre_name_is_unique(db):
    db.add(Genre(name=GENRE_CATALOG[0]))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.database.conf.dependencies import get_db
from test.conf.conf_database import (
    setup_test_db,
    teardown_test_db,
    override_get_db,
    TestingSessionLocal,
)
from test.conf.seed import seed_database, SEED_PASSWORD

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    setup_test_db()
    yield
    teardown_test_db()

@pytest.fixture
def client():
    print(">>> fixture client")
    return TestClient(app)


@pytest.fixture
def db():
    """Direct session against the test database, to assert on things the API
    never returns (for example the password hash)."""
    session = TestingSessionLocal()
    yield session
    session.close()  # if left open, drop_all() would block waiting for it


@pytest.fixture
def seed():
    """Fill the database with 10 users, 20 posts and 60 comments.
    Only runs for the tests that ask for it as a parameter."""
    session = TestingSessionLocal()
    try:
        return seed_database(session)
    finally:
        session.close()


@pytest.fixture
def login(client):
    """Factory fixture: it returns a FUNCTION, so a single test can log in as
    several different users:

        headers = login("john0")
        client.get("/users/me", headers=headers)
    """

    def _login(username: str, password: str = SEED_PASSWORD) -> dict:
        response = client.post(
            "/users/login", data={"username": username, "password": password}
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login

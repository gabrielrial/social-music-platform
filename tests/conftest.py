import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.conf.dependencies import get_db
from tests.conf_database import (
    setup_test_db,
    teardown_test_db,
    override_get_db,
)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    setup_test_db()
    yield
    teardown_test_db()
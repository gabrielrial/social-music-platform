import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.conf.alch_conf import Base, DATABASE_URL as APP_DATABASE_URL
from app.database.models import user, post, comment

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://admin:password@localhost:5433/forumdb_test"
)

# Every test drops all tables. Refuse to run against the app's database.
if TEST_DATABASE_URL == APP_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL points to the application database. "
        "Refusing to run tests: they would drop its tables."
    )


engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_test_db():
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    Base.metadata.drop_all(bind=engine)
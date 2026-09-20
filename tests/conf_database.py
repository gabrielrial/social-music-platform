from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.conf.alch_conf import Base
from app.database.models import user, post, comment

POSTGRESQL_DATABASE_URL = "postgresql://admin:password@localhost:5433/forumdb_test"
from sqlalchemy.pool import StaticPool

engine = create_engine(POSTGRESQL_DATABASE_URL) 

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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models.user import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

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
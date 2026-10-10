import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Must be set before app.main is imported: keeps the app from migrating/purging
# whatever database DATABASE_URL points at.
os.environ["RUN_STARTUP_TASKS"] = "0"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured")

os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

from app.database import Base, get_db
from app.main import app
from app.services.rate_limit import limiter

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    with test_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

# Fixture for FastAPI TestClient
@pytest.fixture(scope="function")
def client(db_session):
    limiter.reset()

    # Override the get_db dependency
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

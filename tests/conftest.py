from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from fastapi.testclient import TestClient
from app.database import get_db, Base
from app.main import app


# Define the test database URL
TEST_DATABASE_URL = "postgresql://admin:admin123@localhost:5433/ragdb_test"

# Create the engine and sessionmaker for the test database
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Fixture for database session
@pytest.fixture(scope="function")
def db_session():
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
    # Override the get_db dependency
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create a TestClient for the FastAPI app
    with TestClient(app) as test_client:
        yield test_client
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base # Adjust this import path if needed
from app.main import app
from app.database.session import get_db # Your dependency for database session
from fastapi.testclient import TestClient
from datetime import datetime, UTC # Add UTC import for consistency

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# Use check_same_thread=False for SQLite in-memory DBs for FastAPI/SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test."""
    Base.metadata.create_all(bind=engine)  # Create tables for this test run
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Drop tables after the test

# Override FastAPI's get_db dependency
@pytest.fixture(scope="function")
def client(db_session):
    """Create a FastAPI test client that uses the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close() # Important for the lifespan of the fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear() # Clear overrides after the test
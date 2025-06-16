# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from fastapi.testclient import TestClient
from app.database.models import Base
from app.database.session import get_db
from dotenv import load_dotenv

# --- Fixture to load .env for tests ---
@pytest.fixture(scope="session", autouse=True)
def load_env_for_tests():
    """
    Loads environment variables from the .env file for testing.
    This ensures SECRET_KEY and other env vars are available to the app during tests.
    """
    load_dotenv()


# Use an in-memory SQLite database for testing. It's destroyed after the tests.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    Provides a test database session for each test.
    It creates tables, starts a transaction, yields the session,
    then rolls back the transaction and drops tables to ensure a clean state.
    """
    # Create all tables for the test database
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    try:
        yield db
    finally:
        transaction.rollback() # Rollback all changes made by the test
        db.close() # Close the session
        connection.close() # Close the connection
        Base.metadata.drop_all(bind=engine) # Drop tables to ensure a completely clean slate


@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    """
    Provides a FastAPI test client that uses the isolated test database session.
    It overrides the application's database dependency to use the test session.
    """
    def override_get_db():
        yield db_session

    # Override the application's database dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # Clean up the dependency override after the test
    app.dependency_overrides.clear() # Clears all overrides
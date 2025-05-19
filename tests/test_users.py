from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app  # Assuming your FastAPI app instance is in main.py
from app.database import models, schemas
from app.database.session import Base, get_db
from app.utils.auth import create_access_token
from datetime import timedelta, datetime
from typing import Generator
from fastapi import Depends
from sqlalchemy import text  # Import the text function
from fastapi import status

# Set up an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Utility function to create a test user and get a token
def create_test_user(db: TestingSessionLocal, is_admin: bool = False):
    user_data = schemas.UserCreateDB(
        username=f"testuser_{datetime.utcnow().timestamp()}",
        email=f"test_{datetime.utcnow().timestamp()}@example.com",
        password_hash="testpassword",
        registration_date=datetime.utcnow(),
        user_age=30,
        is_admin=is_admin
    )
    db_user = models.User(**user_data.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return db_user, access_token

def test_create_user():
    db = TestingSessionLocal()
    user_data = {
        "username": "newtestuser",
        "email": "newtest@example.com",
        "password": "password123",
        "user_age": 28
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == "newtestuser"
    assert content["email"] == "newtest@example.com"
    assert content["user_age"] == 28
    assert "user_id" in content
    db_user = db.query(models.User).filter(models.User.username == "newtestuser").first()
    assert db_user is not None
    db.close()

def test_create_user_duplicate_username():
    db = TestingSessionLocal()
    # Create a user first
    user_data_1 = schemas.UserCreateDB(
        username="duplicateuser",
        email="dup1@example.com",
        password_hash="hash1",
        registration_date=datetime.utcnow(),
        user_age=25,
        is_admin=False
    )
    db_user_1 = models.User(**user_data_1.dict())
    db.add(db_user_1)
    db.commit()

    # Try to create another user with the same username
    user_data_2 = {
        "username": "duplicateuser",
        "email": "dup2@example.com",
        "password": "anotherpassword",
        "user_age": 30
    }
    response = client.post("/users/", json=user_data_2)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    content = response.json()
    assert content["detail"] == "Username already registered"
    db.close()

def test_create_user_duplicate_email():
    db = TestingSessionLocal()
    # Create a user first
    user_data_1 = schemas.UserCreateDB(
        username="uniqueuser",
        email="same@example.com",
        password_hash="hash1",
        registration_date=datetime.utcnow(),
        user_age=25,
        is_admin=False
    )
    db_user_1 = models.User(**user_data_1.dict())
    db.add(db_user_1)
    db.commit()

    # Try to create another user with the same email
    user_data_2 = {
        "username": "anotheruser",
        "email": "same@example.com",
        "password": "anotherpassword",
        "user_age": 30
    }
    response = client.post("/users/", json=user_data_2)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    content = response.json()
    assert content["detail"] == "Email already registered"
    db.close()

def test_read_current_user_authenticated():
    db = TestingSessionLocal()
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == test_user.username
    assert content["email"] == test_user.email
    assert content["user_id"] == test_user.user_id
    db.close()

def test_read_user_by_id_authenticated():
    db = TestingSessionLocal()
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"/users/{test_user.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == test_user.username
    assert content["email"] == test_user.email
    assert content["user_id"] == test_user.user_id
    db.close()

def test_read_user_by_id_not_found_authenticated():
    db = TestingSessionLocal()
    _, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/9999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.json()
    assert content["detail"] == "User not found"
    db.close()

def test_read_users_not_admin():
    db = TestingSessionLocal()
    _, access_token = create_test_user(db, is_admin=False)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    content = response.json()
    assert content["detail"] == "Not authorized to read all users."
    db.close()

def test_read_users_admin():
    db = TestingSessionLocal()
    # Create two test users
    admin_user, admin_token = create_test_user(db, is_admin=True)
    user1, _ = create_test_user(db, is_admin=False)
    user2, _ = create_test_user(db, is_admin=False)

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert len(content) >= 3  # Admin + 2 other users
    assert any(user["user_id"] == admin_user.user_id for user in content)
    assert any(user["user_id"] == user1.user_id for user in content)
    assert any(user["user_id"] == user2.user_id for user in content)
    db.close()

def test_update_user_not_authorized():
    db = TestingSessionLocal()
    user1, token1 = create_test_user(db)
    user2, _ = create_test_user(db)
    headers = {"Authorization": f"Bearer {token1}"}
    updated_data = {"username": "updateduser"}
    response = client.put(f"/users/{user2.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    content = response.json()
    assert content["detail"] == "Not authorized to update this user"
    db.close()

def test_update_user_authorized_self():
    db = TestingSessionLocal()
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    updated_data = {"username": "newusername", "user_age": 35}
    response = client.put(f"/users/{test_user.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["user_id"] == test_user.user_id
    assert content["username"] == "newusername"
    assert content["user_age"] == 35
    db_user = db.query(models.User).filter(models.User.user_id == test_user.user_id).first()
    assert db_user.username == "newusername"
    assert db_user.user_age == 35
    db.close()
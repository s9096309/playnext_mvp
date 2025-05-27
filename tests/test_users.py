import pytest  # Import pytest for fixtures
import uuid  # For generating unique parts of usernames/emails
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session  # Import Session for type hinting
from datetime import datetime, timedelta
from app.main import app
from app.database import models, schemas
from app.utils.auth import create_access_token
from app.database import user_crud
from app.database.user_crud import get_user_by_email, update_user, delete_user # <--- Import specific functions

# Removed direct database setup imports (create_engine, sessionmaker, Base, get_db)
# as they are handled by conftest.py

# --- Helper function for tests (using fixtures) ---

# db_session and client fixtures are provided by tests/conftest.py

def create_test_user(db: Session, is_admin: bool = False):
    """Helper to create a user and return user object and access token."""
    # Use UUID for unique username and email to prevent IntegrityError
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user_data = schemas.UserCreateDB(
        username=username,
        email=email,
        password_hash="testpassword",  # In a real app, this would be hashed
        registration_date=datetime.utcnow(),
        user_age=30,
        is_admin=is_admin
    )
    db_user = models.User(**user_data.model_dump())  # Use .model_dump() for Pydantic V2
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return db_user, access_token


# --- Test Cases ---

def test_create_user(db_session: Session, client: TestClient):
    db = db_session  # Use the fixture-provided session
    user_data = {
        "username": "newtestuser",
        "email": "newtest@example.com",
        "password": "password123",  # This will be hashed by your FastAPI endpoint
        "user_age": 28
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == "newtestuser"
    assert content["email"] == "newtest@example.com"
    assert content["user_age"] == 28
    assert "user_id" in content

    # Verify directly from the database
    db_user = db.query(models.User).filter(models.User.username == "newtestuser").first()
    assert db_user is not None
    assert db_user.email == "newtest@example.com"


def test_create_user_duplicate_username(db_session: Session, client: TestClient):
    db = db_session
    # Use the helper to create a user, ensuring unique base values
    duplicate_username_base = f"duplicateuser_{uuid.uuid4().hex[:4]}"
    user_data_1_schema = schemas.UserCreateDB(
        username=duplicate_username_base,
        email=f"{duplicate_username_base}_1@example.com",
        password_hash="hash1",
        registration_date=datetime.utcnow(),
        user_age=25,
        is_admin=False
    )
    db_user_1 = models.User(**user_data_1_schema.model_dump())
    db.add(db_user_1)
    db.commit()
    db.refresh(db_user_1)  # Refresh to get ID if needed, though not strictly here

    # Try to create another user with the same username via API
    user_data_2 = {
        "username": duplicate_username_base,  # This username already exists
        "email": f"{duplicate_username_base}_2@example.com",  # Unique email
        "password": "anotherpassword",
        "user_age": 30
    }
    response = client.post("/users/", json=user_data_2)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    content = response.json()
    assert content["detail"] == "Username already registered"


def test_create_user_duplicate_email(db_session: Session, client: TestClient):
    db = db_session
    # Create a user first with a unique username but a specific email
    duplicate_email_base = f"same_{uuid.uuid4().hex[:4]}@example.com"
    user_data_1_schema = schemas.UserCreateDB(
        username=f"uniqueuser_{uuid.uuid4().hex[:4]}",
        email=duplicate_email_base,  # This email will be duplicated
        password_hash="hash1",
        registration_date=datetime.utcnow(),
        user_age=25,
        is_admin=False
    )
    db_user_1 = models.User(**user_data_1_schema.model_dump())
    db.add(db_user_1)
    db.commit()
    db.refresh(db_user_1)

    # Try to create another user with the same email via API
    user_data_2 = {
        "username": f"anotheruser_{uuid.uuid4().hex[:4]}",  # Unique username
        "email": duplicate_email_base,  # Duplicate email
        "password": "anotherpassword",
        "user_age": 30
    }
    response = client.post("/users/", json=user_data_2)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    content = response.json()
    assert content["detail"] == "Email already registered"


def test_read_current_user_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == test_user.username
    assert content["email"] == test_user.email
    assert content["user_id"] == test_user.user_id


def test_read_user_by_id_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"/users/{test_user.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["username"] == test_user.username
    assert content["email"] == test_user.email
    assert content["user_id"] == test_user.user_id


def test_read_user_by_id_not_found_authenticated(db_session: Session, client: TestClient):
    db = db_session
    _, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/9999999999", headers=headers)  # Use a very large, unlikely ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.json()
    assert content["detail"] == "User not found"


def test_read_users_not_admin(db_session: Session, client: TestClient):
    db = db_session
    # Create a non-admin user
    _, access_token = create_test_user(db, is_admin=False)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    content = response.json()
    assert content["detail"] == "Not authorized to read all users."


def test_read_users_admin(db_session: Session, client: TestClient):
    db = db_session
    # Create two test users, one of which is an admin
    admin_user, admin_token = create_test_user(db, is_admin=True)
    user1, _ = create_test_user(db, is_admin=False)
    user2, _ = create_test_user(db, is_admin=False)

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    # There should be at least 3 users (admin + 2 created)
    assert len(content) >= 3
    assert any(user["user_id"] == admin_user.user_id for user in content)
    assert any(user["user_id"] == user1.user_id for user in content)
    assert any(user["user_id"] == user2.user_id for user in content)


def test_update_user_not_authorized(db_session: Session, client: TestClient):
    db = db_session
    # User1 tries to update User2
    user1, token1 = create_test_user(db)
    user2, _ = create_test_user(db)
    headers = {"Authorization": f"Bearer {token1}"}
    updated_data = {"username": "updateduser"}
    response = client.put(f"/users/{user2.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    content = response.json()
    assert content["detail"] == "Not authorized to update this user"


def test_update_user_authorized_self(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    updated_data = {"username": "newusername", "user_age": 35}
    response = client.put(f"/users/{test_user.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["user_id"] == test_user.user_id
    assert content["username"] == "newusername"
    assert content["user_age"] == 35

    # Verify the update in the database
    db_user = db.query(models.User).filter(models.User.user_id == test_user.user_id).first()
    assert db_user.username == "newusername"
    assert db_user.user_age == 35


def test_update_user_admin_authorized(db_session: Session, client: TestClient):
    db = db_session
    admin_user, admin_token = create_test_user(db, is_admin=True)
    user_to_update, _ = create_test_user(db, is_admin=False)
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"username": "adminupdateduser", "email": "adminupdate@example.com"}
    response = client.put(f"/users/{user_to_update.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["user_id"] == user_to_update.user_id
    assert content["username"] == "adminupdateduser"
    assert content["email"] == "adminupdate@example.com"

    db_user = db.query(models.User).filter(models.User.user_id == user_to_update.user_id).first()
    assert db_user.username == "adminupdateduser"
    assert db_user.email == "adminupdate@example.com"


def test_delete_user_not_authorized(db_session: Session, client: TestClient):
    db = db_session
    user1, token1 = create_test_user(db)
    user2, _ = create_test_user(db)
    headers = {"Authorization": f"Bearer {token1}"}
    response = client.delete(f"/users/{user2.user_id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    content = response.json()
    assert content["detail"] == "Not authorized to delete this user"


def test_delete_user_authorized_self(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete(f"/users/{test_user.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["message"] == "User deleted successfully"

    db_user = db.query(models.User).filter(models.User.user_id == test_user.user_id).first()
    assert db_user is None


def test_delete_user_admin_authorized(db_session: Session, client: TestClient):
    db = db_session
    admin_user, admin_token = create_test_user(db, is_admin=True)
    user_to_delete, _ = create_test_user(db, is_admin=False)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete(f"/users/{user_to_delete.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["message"] == "User deleted successfully"

    db_user = db.query(models.User).filter(models.User.user_id == user_to_delete.user_id).first()
    assert db_user is None
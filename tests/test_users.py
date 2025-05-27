import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from test_helpers import create_test_user, create_test_game

def test_create_user(db_session: Session, client: TestClient):
    db = db_session  # Use the fixture-provided session
    user_data = {
        "username": "newtestuser",
        "email": "newtest@example.com",
        "password": "password123",
        "user_age": 28
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK  # Expect 200 OK on success
    response_data = response.json()
    assert response_data["username"] == "newtestuser"
    assert response_data["email"] == "newtest@example.com"
    assert response_data["user_age"] == 28
    assert "user_id" in response_data
    assert "registration_date" in response_data
    assert response_data["is_admin"] is False


def test_create_user_duplicate_username(db_session: Session, client: TestClient):
    db = db_session
    # Create the first user
    create_test_user(db, username="duplicateuser", email="first@example.com")

    # Try to create another user with the same username
    user_data = {
        "username": "duplicateuser",
        "email": "second@example.com",
        "password": "password123",
        "user_age": 25
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Username already registered"}


def test_create_user_duplicate_email(db_session: Session, client: TestClient):
    db = db_session
    # Create the first user
    create_test_user(db, username="user_one", email="duplicate@example.com")

    # Try to create another user with the same email
    user_data = {
        "username": "user_two",
        "email": "duplicate@example.com",
        "password": "password123",
        "user_age": 30
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Email already registered"}


def test_read_current_user_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username


def test_read_user_by_id_authenticated(db_session: Session, client: TestClient):
    db = db_session
    # Create a user to be read
    user_to_read, _ = create_test_user(db, username="user_to_read", email="read@example.com")

    # Create an authenticated user (can be the same or different, depends on permissions)
    auth_user, auth_token = create_test_user(db, username="auth_reader", email="auth_read@example.com")
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = client.get(f"/users/{user_to_read.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user_to_read.username


def test_read_user_by_id_not_found_authenticated(db_session: Session, client: TestClient):
    db = db_session
    auth_user, auth_token = create_test_user(db, username="auth_nf", email="auth_nf@example.com")
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/users/9999999999", headers=headers)  # Using a very large ID unlikely to exist
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "User not found"}


def test_read_users_not_admin(db_session: Session, client: TestClient):
    db = db_session
    # Create a non-admin user
    non_admin_user, non_admin_token = create_test_user(db, is_admin=False)
    headers = {"Authorization": f"Bearer {non_admin_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authorized to access this resource"}


def test_read_users_admin(db_session: Session, client: TestClient):
    db = db_session
    # Create an admin user
    admin_user, admin_token = create_test_user(db, is_admin=True)
    # Create some other users
    create_test_user(db, username="user_a", email="a@example.com")
    create_test_user(db, username="user_b", email="b@example.com")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    users_data = response.json()
    assert isinstance(users_data, list)
    assert len(users_data) >= 3  # Admin user + 2 created users
    assert any(u["username"] == "user_a" for u in users_data)
    assert any(u["username"] == "user_b" for u in users_data)


def test_update_user_not_authorized(db_session: Session, client: TestClient):
    db = db_session
    # User1 tries to update User2
    user1, token1 = create_test_user(db, username="user1_upd_auth", email="u1_upd@example.com")
    user2, _ = create_test_user(db, username="user2_upd_auth", email="u2_upd@example.com")
    headers = {"Authorization": f"Bearer {token1}"}
    updated_data = {"username": "updateduser_unauth"}  # Payload for update
    response = client.put(f"/users/{user2.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN  # Expect 403, not 422
    assert response.json() == {"detail": "Not authorized to update this user"}


def test_update_user_authorized_self(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db, username="self_update_user", email="self_update@example.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    updated_data = {"username": "newusername_self", "user_age": 35}  # Payload for update
    response = client.put(f"/users/{test_user.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_200_OK  # Expect 200 OK
    response_data = response.json()
    assert response_data["username"] == "newusername_self"
    assert response_data["user_age"] == 35


def test_update_user_admin_authorized(db_session: Session, client: TestClient):
    db = db_session
    admin_user, admin_token = create_test_user(db, is_admin=True, username="admin_upd", email="admin_upd@example.com")
    user_to_update, _ = create_test_user(db, username="target_upd", email="target_upd@example.com")
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"user_age": 40, "is_admin": True}  # Admin can change is_admin
    response = client.put(f"/users/{user_to_update.user_id}", headers=headers, json=updated_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["user_id"] == user_to_update.user_id
    assert response_data["user_age"] == 40
    assert response_data["is_admin"] is True


def test_delete_user_not_authorized(db_session: Session, client: TestClient):
    db = db_session
    user1, token1 = create_test_user(db, username="user1_del_auth", email="u1_del@example.com")
    user2, _ = create_test_user(db, username="user2_del_auth", email="u2_del@example.com")
    headers = {"Authorization": f"Bearer {token1}"}
    response = client.delete(f"/users/{user2.user_id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authorized to delete this user"}


def test_delete_user_authorized_self(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db, username="self_delete_user", email="self_delete@example.com")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.delete(f"/users/{test_user.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["detail"] == "User deleted successfully"  # Changed from "message" to "detail"


def test_delete_user_admin_authorized(db_session: Session, client: TestClient):
    db = db_session
    admin_user, admin_token = create_test_user(db, is_admin=True, username="admin_del", email="admin_del@example.com")
    user_to_delete, _ = create_test_user(db, is_admin=False, username="target_del", email="target_del@example.com")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete(f"/users/{user_to_delete.user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["detail"] == "User deleted successfully"  # Changed from "message" to "detail"
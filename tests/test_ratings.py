import pytest
import uuid  # For generating unique IDs
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session  # Import Session for type hinting
from datetime import datetime, timedelta, date  # Ensure date is imported
from app.main import app
from app.database import models, schemas, crud


# No longer need to import Base or get_db directly here for test setup

# --- Helper functions for tests (using fixtures) ---

# db_session and client fixtures are provided by tests/conftest.py

def create_test_user(db: Session, is_admin: bool = False):
    """Helper to create a user and return user object and access token."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"  # Use UUID for unique username
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"  # Use UUID for unique email
    user_data = schemas.UserCreateDB(
        username=username,
        email=email,
        password_hash="testpasswordhash",  # Consider hashing this in real app
        registration_date=datetime.utcnow(),
        user_age=30,
        is_admin=is_admin
    )
    db_user = models.User(**user_data.model_dump())  # Use .model_dump()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    from app.utils.auth import \
        create_access_token  # Import locally to avoid circular imports if auth.py depends on models
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return db_user, access_token


def create_test_game(db: Session, igdb_id: int = None):
    """Helper to create a game with a unique IGDB ID."""
    if igdb_id is None:
        igdb_id = uuid.uuid4().int % (10 ** 9)  # Generate a large random int for uniqueness
    game_name = f"Test Game {igdb_id}"
    game_data = schemas.GameCreate(
        game_name=game_name,
        genre="Test Genre",
        release_date=date(2023, 1, 1),  # Use date for release_date
        platform="Test Platform",
        igdb_id=igdb_id
    )
    return crud.create_game(db=db, game=game_data)


# --- Test Cases ---

def test_create_rating_unauthenticated(client):  # Only client needed
    rating_payload = {
        "game_id": 36,  # This ID needs to exist in the DB for a valid request, though it won't matter for 401
        "rating": 10,
        "comment": "a very SOLID game",
        "rating_date": datetime.utcnow().isoformat()
    }
    response = client.post("/ratings/me/", json=rating_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


def test_create_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session  # Use the fixture-provided session

    test_user, access_token = create_test_user(db)
    # Ensure game has a unique ID for this specific test
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))
    headers = {"Authorization": f"Bearer {access_token}"}
    rating_payload = {
        "game_id": test_game.game_id,  # Use the ID of the created game
        "rating": 8,
        "comment": "This game is awesome!",
        "rating_date": datetime.utcnow().isoformat()
    }
    response = client.post("/ratings/me/", headers=headers, json=rating_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["user_id"] == test_user.user_id
    assert response_data["game_id"] == test_game.game_id
    assert response_data["rating"] == 8
    assert response_data["comment"] == "This game is awesome!"
    assert "rating_id" in response_data


def test_get_ratings(db_session: Session, client: TestClient):
    db = db_session  # Use the fixture-provided session

    # Create some test ratings
    user1, _ = create_test_user(db, is_admin=False)  # Use helper
    game1 = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))  # Unique ID
    rating_data_1 = schemas.RatingCreate(
        user_id=user1.user_id,
        game_id=game1.game_id,
        rating=4.0,
        comment="Comment for game 1",
        rating_date=datetime.utcnow()
    )
    crud.create_rating(db=db, rating=rating_data_1)

    user2, _ = create_test_user(db, is_admin=False)  # Use helper
    game2 = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))  # Another unique ID
    rating_data_2 = schemas.RatingCreate(
        user_id=user2.user_id,
        game_id=game2.game_id,
        rating=5.0,
        comment="Comment for game 2",
        rating_date=datetime.utcnow()
    )
    crud.create_rating(db=db, rating=rating_data_2)

    # Now make the API call to get all ratings
    response = client.get("/ratings/")
    assert response.status_code == status.HTTP_200_OK
    ratings_data = response.json()

    # Assert that the created ratings are present in the response
    assert len(ratings_data) >= 2  # Assuming no other ratings exist from previous setup
    assert any(r["user_id"] == user1.user_id and r["game_id"] == game1.game_id for r in ratings_data)
    assert any(r["user_id"] == user2.user_id and r["game_id"] == game2.game_id for r in ratings_data)
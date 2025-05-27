import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, UTC
from app.main import app
from app.database import models, schemas, crud
from app.database import user_crud

# IMPORT THE HELPER FUNCTIONS
from test_helpers import create_test_user, create_test_game

# db_session and client fixtures are provided by tests/conftest.py


# --- Test Cases ---

def test_create_rating_unauthenticated(client):
    rating_payload = {
        "game_id": 999,
        "rating": 10,
        "comment": "a very SOLID game",
        "rating_date": datetime.now(UTC).isoformat()
    }
    response = client.post("/ratings/me/", json=rating_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


def test_create_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session

    test_user, access_token = create_test_user(db)
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))
    headers = {"Authorization": f"Bearer {access_token}"}
    rating_payload = {
        "game_id": test_game.game_id,
        "rating": 8,
        "comment": "This game is awesome!",
        "rating_date": datetime.now(UTC).isoformat()
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
    db = db_session

    # Create some test ratings
    user1, _ = create_test_user(db, username="user1_ratings_test", email="user1_ratings@example.com")
    game1 = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9), game_name="Game Alpha")
    rating_data_1 = schemas.RatingCreate(
        user_id=user1.user_id,
        game_id=game1.game_id,
        rating=4.0,
        comment="Comment for game Alpha",
        rating_date=datetime.now(UTC)
    )
    crud.create_rating(db=db, rating=rating_data_1)

    user2, _ = create_test_user(db, username="user2_ratings_test", email="user2_ratings@example.com")
    game2 = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9), game_name="Game Beta")
    rating_data_2 = schemas.RatingCreate(
        user_id=user2.user_id,
        game_id=game2.game_id,
        rating=5.0,
        comment="Comment for game Beta",
        rating_date=datetime.now(UTC)
    )
    crud.create_rating(db=db, rating=rating_data_2)

    # Create an authenticated user to get a token for the endpoint that likely requires auth
    auth_user, auth_token = create_test_user(db, username="auth_user_for_ratings_get", email="auth_ratings_get@example.com")
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Now make the API call to get all ratings with authentication
    response = client.get("/ratings/", headers=headers) # Provide auth headers
    assert response.status_code == status.HTTP_200_OK
    ratings_data = response.json()

    assert len(ratings_data) >= 2
    assert any(r["user_id"] == user1.user_id and r["game_id"] == game1.game_id for r in ratings_data)
    assert any(r["user_id"] == user2.user_id and r["game_id"] == game2.game_id for r in ratings_data)
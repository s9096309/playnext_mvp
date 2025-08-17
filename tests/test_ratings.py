# tests/test_ratings.py

import pytest
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, UTC  # Ensure UTC is imported
from application import application as app
from database import crud
from database import schemas

from test_helpers import create_test_user, create_test_game

# --- Test Cases ---

def test_create_rating_unauthenticated(client):
    rating_payload = {
        "game_id": 999,
        "rating": 10,
        "comment": "a very SOLID game",
        "rating_date": datetime.now(UTC).isoformat()
    }
    response = client.post("/users/me/ratings/", json=rating_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


def test_create_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session

    test_user, access_token = create_test_user(db)
    test_user_id = test_user.user_id
    # Create a unique game for this test
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9),
                                 game_name="Auth Create Game " + str(uuid.uuid4()))
    test_game_id = test_game.game_id

    headers = {"Authorization": f"Bearer {access_token}"}
    rating_payload = {
        "game_id": test_game_id,
        "rating": 8,
        "comment": "This game is awesome!",
        "rating_date": datetime.now(UTC).isoformat()
    }
    response = client.post("/users/me/ratings/", headers=headers, json=rating_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["user_id"] == test_user_id
    assert response_data["game_id"] == test_game_id  # Ensure game_id is also returned
    assert response_data["rating"] == 8.0
    assert response_data["comment"] == "This game is awesome!"
    assert "rating_id" in response_data
    assert "rating_date" in response_data
    assert "updated_at" in response_data  # Ensure updated_at is present, even if null

    # Assert nested game data is present
    assert "game" in response_data
    assert response_data["game"]["game_id"] == test_game_id
    assert response_data["game"]["game_name"] == test_game.game_name
    assert "image_url" in response_data["game"]


def test_get_ratings(db_session: Session, client: TestClient):
    db = db_session

    # Create an authenticated user to get a token for the endpoint
    auth_user, auth_token = create_test_user(db, username="auth_user_for_ratings_get",
                                             email="auth_ratings_get@example.com")
    auth_user_id = auth_user.user_id  # ID of the user whose ratings we expect to retrieve

    # Create games (use unique names to avoid conflicts in a real database, though test helpers should clean)
    game_alpha = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9),
                                  game_name="Test Game Alpha " + str(uuid.uuid4()))
    game_beta = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9),
                                 game_name="Test Game Beta " + str(uuid.uuid4()))

    # Create ratings linked to the AUTHENTICATED user (auth_user_id)
    rating_data_1 = schemas.RatingCreate(
        user_id=auth_user_id,  # Crucial: Link to the authenticated user
        game_id=game_alpha.game_id,
        rating=4.0,
        comment="Comment for Test Game Alpha",
        rating_date=datetime.now(UTC)
    )
    crud.create_rating(db=db, rating=rating_data_1)

    rating_data_2 = schemas.RatingCreate(
        user_id=auth_user_id,  # Crucial: Link to the authenticated user
        game_id=game_beta.game_id,
        rating=5.0,
        comment="Comment for Test Game Beta",
        rating_date=datetime.now(UTC)
    )
    crud.create_rating(db=db, rating=rating_data_2)

    # (Optional) Create a rating for a different user, which should NOT be returned
    other_user, _ = create_test_user(db, username="other_user_ratings_test", email="other_user_ratings@example.com")
    other_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9), game_name="Other Game " + str(uuid.uuid4()))
    rating_data_other = schemas.RatingCreate(
        user_id=other_user.user_id,
        game_id=other_game.game_id,
        rating=2.0,
        comment="Should not be seen",
        rating_date=datetime.now(UTC)
    )
    crud.create_rating(db=db, rating=rating_data_other)

    headers = {"Authorization": f"Bearer {auth_token}"}

    # Fetch ratings for the authenticated user using the correct endpoint
    response = client.get("/users/me/ratings", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    ratings_data = response.json()

    # The authenticated user should only see their own 2 ratings
    assert len(ratings_data) == 2

    # Verify the structure and content of the ratings received
    rating1_found = False
    rating2_found = False

    for r in ratings_data:
        # Every rating returned should belong to the authenticated user
        assert r["user_id"] == auth_user_id
        assert "game" in r  # Ensure the nested game object is present

        if r["game_id"] == game_alpha.game_id:
            assert r["rating"] == 4.0
            assert r["comment"] == "Comment for Test Game Alpha"
            # Verify nested game data
            assert r["game"]["game_id"] == game_alpha.game_id
            assert r["game"]["game_name"] == game_alpha.game_name
            assert "image_url" in r["game"]
            rating1_found = True
        elif r["game_id"] == game_beta.game_id:
            assert r["rating"] == 5.0
            assert r["comment"] == "Comment for Test Game Beta"
            # Verify nested game data
            assert r["game"]["game_id"] == game_beta.game_id
            assert r["game"]["game_name"] == game_beta.game_name
            assert "image_url" in r["game"]
            rating2_found = True
        else:
            pytest.fail(f"Unexpected rating found for game_id: {r['game_id']}")

    assert rating1_found and rating2_found, "Both expected ratings for the authenticated user were not found."


def test_update_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    # Create an initial rating
    initial_rating = schemas.RatingCreate(
        user_id=test_user.user_id,
        game_id=test_game.game_id,
        rating=7.0,
        comment="Initial comment",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, initial_rating)

    headers = {"Authorization": f"Bearer {access_token}"}
    update_payload = {
        "rating": 9.0,
        "comment": "Updated comment!"
    }

    response = client.put(f"/users/me/ratings/{created_rating.rating_id}", headers=headers, json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["rating"] == 9.0
    assert response_data["comment"] == "Updated comment!"
    assert response_data["rating_id"] == created_rating.rating_id
    assert response_data["user_id"] == test_user.user_id
    assert response_data["game_id"] == test_game.game_id
    assert response_data["updated_at"] is not None  # Check that updated_at is populated on update

    # Verify nested game data is still there
    assert "game" in response_data
    assert response_data["game"]["game_id"] == test_game.game_id
    assert response_data["game"]["game_name"] == test_game.game_name


def test_update_rating_unauthorized_other_user(db_session: Session, client: TestClient):
    db = db_session
    user1, _ = create_test_user(db, username="user1_update_test")
    user2, access_token_user2 = create_test_user(db, username="user2_update_test")
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    # User1 creates a rating
    initial_rating = schemas.RatingCreate(
        user_id=user1.user_id,
        game_id=test_game.game_id,
        rating=7.0,
        comment="User1's rating",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, initial_rating)

    headers = {"Authorization": f"Bearer {access_token_user2}"}  # User2's token
    update_payload = {"rating": 10.0}

    # User2 tries to update User1's rating
    response = client.put(f"/users/me/ratings/{created_rating.rating_id}", headers=headers, json=update_payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN  # Or 404 if not found (less likely)
    assert response.json() == {"detail": "Not authorized to update this rating."}

def test_delete_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    # Create a rating to delete
    initial_rating = schemas.RatingCreate(
        user_id=test_user.user_id,
        game_id=test_game.game_id,
        rating=6.0,
        comment="To be deleted",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, initial_rating)

    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.delete(f"/users/me/ratings/{created_rating.rating_id}", headers=headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT  # No content for successful delete

    # Verify it's deleted
    deleted_rating = crud.get_rating(db, created_rating.rating_id)
    assert deleted_rating is None


def test_delete_rating_unauthorized_other_user(db_session: Session, client: TestClient):
    db = db_session
    user1, _ = create_test_user(db, username="user1_delete_test")
    user2, access_token_user2 = create_test_user(db, username="user2_delete_test")
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    # User1 creates a rating
    initial_rating = schemas.RatingCreate(
        user_id=user1.user_id,
        game_id=test_game.game_id,
        rating=7.0,
        comment="User1's rating to delete",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, initial_rating)

    headers = {"Authorization": f"Bearer {access_token_user2}"}  # User2's token

    # User2 tries to delete User1's rating
    response = client.delete(f"/users/me/ratings/{created_rating.rating_id}", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN  # Or 404
    assert response.json() == {"detail": "Not authorized to delete this rating."}


def test_create_duplicate_rating_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    headers = {"Authorization": f"Bearer {access_token}"}
    rating_payload = {
        "game_id": test_game.game_id,
        "rating": 8,
        "comment": "First rating",
        "rating_date": datetime.now(UTC).isoformat()
    }

    response1 = client.post("/users/me/ratings/", headers=headers, json=rating_payload)
    assert response1.status_code == status.HTTP_200_OK

    # Try to create another rating for the same user and game
    response2 = client.post("/users/me/ratings/", headers=headers, json=rating_payload)
    assert response2.status_code == status.HTTP_409_CONFLICT  # Expecting conflict for duplicate
    assert response2.json() == {"detail": "You have already rated this game. Please use the PUT method to update it."}


def test_get_rating_by_id_authenticated(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9), game_name="Test Game By ID")

    rating_data = schemas.RatingCreate(
        user_id=test_user.user_id,
        game_id=test_game.game_id,
        rating=7.5,
        comment="Specific rating test",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, rating_data)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get(f"/users/me/ratings/{created_rating.rating_id}", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["rating_id"] == created_rating.rating_id
    assert response_data["user_id"] == test_user.user_id
    assert response_data["game_id"] == test_game.game_id
    assert response_data["rating"] == 7.5
    assert response_data["comment"] == "Specific rating test"
    assert "game" in response_data
    assert response_data["game"]["game_name"] == "Test Game By ID"
    assert "image_url" in response_data["game"]


def test_get_rating_by_id_not_found(db_session: Session, client: TestClient):
    db = db_session
    test_user, access_token = create_test_user(db)
    headers = {"Authorization": f"Bearer {access_token}"}

    non_existent_id = 99999
    response = client.get(f"/users/me/ratings/{non_existent_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Rating not found."}


def test_get_rating_by_id_unauthorized_other_user(db_session: Session, client: TestClient):
    db = db_session
    user1, _ = create_test_user(db, username="user1_get_id_test")
    user2, access_token_user2 = create_test_user(db, username="user2_get_id_test")
    test_game = create_test_game(db, igdb_id=uuid.uuid4().int % (10 ** 9))

    rating_data = schemas.RatingCreate(
        user_id=user1.user_id,
        game_id=test_game.game_id,
        rating=8.0,
        comment="User1's rating",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db, rating_data)

    headers = {"Authorization": f"Bearer {access_token_user2}"}  # User2's token
    response = client.get(f"/users/me/ratings/{created_rating.rating_id}", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authorized to view this rating."}
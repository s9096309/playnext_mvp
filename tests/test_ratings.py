from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.database import models, schemas, crud
from app.database.session import Base, get_db
from datetime import datetime, timedelta
from typing import Generator
from fastapi import Depends

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

# Utility function to create a test user and get a token (if not already defined)
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
    from app.utils.auth import create_access_token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return db_user, access_token

def create_test_game(db: TestingSessionLocal, igdb_id: int = 999):
    game_data = schemas.GameCreate(
        game_name=f"Test Game {igdb_id}",
        genre="Test Genre",
        release_date=datetime.utcnow().date(),
        platform="Test Platform",
        igdb_id=igdb_id
    )
    return crud.create_game(db=db, game=game_data)

def test_create_rating_unauthenticated():
    rating_payload = {
        "game_id": 36,
        "rating": 10,
        "comment": "a very SOLID game",
        "rating_date": datetime.utcnow().isoformat()
    }
    response = client.post("/ratings/me/", json=rating_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}

def test_create_rating_authenticated():
    db = TestingSessionLocal()
    try:
        test_user, access_token = create_test_user(db)
        test_game = create_test_game(db, igdb_id=36)  # Create the game with the specified ID
        headers = {"Authorization": f"Bearer {access_token}"}
        rating_payload = {
            "game_id": test_game.game_id,  # Use the ID of the created game
            "rating": 8,  # Use a different rating value for clarity
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
    finally:
        db.close()

def test_get_ratings():
    db = TestingSessionLocal()
    try:
        # Create some test ratings
        user1_data = schemas.UserCreateDB(...)
        user1 = crud.create_user(db=db, user=user1_data)
        game1_data = schemas.GameCreate(..., igdb_id=111)  # Unique ID
        game1 = crud.create_game(db=db, game=game1_data)
        rating_data_1 = schemas.RatingCreate(...)
        crud.create_rating(db=db, rating=rating_data_1)

        user2_data = schemas.UserCreateDB(...)
        user2 = crud.create_user(db=db, user=user2_data)
        game2_data = schemas.GameCreate(..., igdb_id=222)  # Another unique ID
        game2 = crud.create_game(db=db, game=game2_data)
        rating_data_2 = schemas.RatingCreate(...)
        crud.create_rating(db=db, rating=rating_data_2)
    finally:
        db.close()
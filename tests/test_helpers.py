# tests/test_helpers.py

import uuid
from datetime import datetime, timedelta, date, UTC
from sqlalchemy.orm import Session

# Import necessary modules from your app
from app.database import schemas, crud
from app.database import user_crud  # For create_test_user
from app.utils.auth import get_password_hash, create_access_token  # For create_test_user


def create_test_user(db: Session, is_admin: bool = False, username: str = None, email: str = None):
    """Helper to create a user and return user object and access token."""
    username = username if username else f"testuser_{uuid.uuid4().hex[:8]}"
    email = email if email else f"test_{uuid.uuid4().hex[:8]}@example.com"

    user_data = schemas.UserCreateDB(
        username=username,
        email=email,
        password_hash=get_password_hash("testpassword123"),  # Hash the password
        registration_date=datetime.now(UTC),
        user_age=30,
        is_admin=is_admin
    )

    db_user = user_crud.create_user(db=db, user=user_data)

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
    return db_user, access_token


def create_test_game(db: Session, igdb_id: int = None, game_name: str = None):
    """Helper to create a game with a unique IGDB ID."""
    if igdb_id is None:
        igdb_id = uuid.uuid4().int % (10 ** 9)
    game_name = game_name if game_name else f"Test Game {igdb_id}_{uuid.uuid4().hex[:4]}"
    game_data = schemas.GameCreate(
        game_name=game_name,
        genre="Test Genre",
        release_date=date(2023, 1, 1),
        platform="Test Platform",
        igdb_id=igdb_id
    )
    return crud.create_game(db=db, game=game_data)
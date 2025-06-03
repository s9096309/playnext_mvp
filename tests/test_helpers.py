# tests/test_helpers.py

from sqlalchemy.orm import Session
from app.database import crud, user_crud, schemas, models
from app.utils.auth import create_access_token, get_password_hash
from datetime import datetime, date, UTC
from typing import Tuple, Optional
import uuid

def create_test_user(db: Session, username: str = None, email: str = None,
                     password: str = "password", is_admin: bool = False) -> Tuple[models.User, str]:
    # Generate unique username and email if not provided
    unique_suffix = uuid.uuid4().hex[:8] # A short, unique hexadecimal string
    if username is None:
        username = f"testuser_{unique_suffix}"
    if email is None:
        email = f"test_{unique_suffix}@example.com"

    user_create_db = schemas.UserCreateDB(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        registration_date=datetime.now(UTC).replace(tzinfo=None), # Ensure naive UTC for DB
        user_age=25,
        is_admin=is_admin
    )
    user = user_crud.create_user(db=db, user=user_create_db)
    db.refresh(user) # Crucial: Ensure user object is refreshed and attached to the session
    access_token = create_access_token(data={"sub": user.username})
    return user, access_token

def create_test_game(db: Session, game_name: str = None, genre: str = "Action",
                     release_date: date = date(2023, 1, 1), platform: str = "PC",
                     igdb_id: Optional[int] = None, image_url: Optional[str] = None,
                     age_rating: Optional[str] = None) -> models.Game:
    if igdb_id is None:
        igdb_id = uuid.uuid4().int % (10**9) # Generate a random unique ID
    if game_name is None:
        game_name = f"Test Game {uuid.uuid4().hex[:8]}" # Make game_name unique

    # Ensure image_url has a default if not provided, for consistency
    if image_url is None:
        image_url = f"http://example.com/game_images/{igdb_id}.jpg"

    game_data = schemas.GameCreate(
        game_name=game_name,
        genre=genre,
        release_date=release_date,
        platform=platform,
        igdb_id=igdb_id,
        image_url=image_url,
        age_rating=age_rating
    )
    game = crud.create_game(db=db, game=game_data)
    db.refresh(game)
    return game
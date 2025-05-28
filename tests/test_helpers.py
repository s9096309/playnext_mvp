# In tests/test_helpers.py

from sqlalchemy.orm import Session
from app.database import crud, user_crud, schemas, models # Ensure models is imported too if you use it directly
from app.utils.auth import create_access_token, get_password_hash
from datetime import datetime, date, UTC
from typing import Tuple, Optional
import uuid

def create_test_user(db: Session, username: str = "testuser", email: str = "test@example.com",
                     password: str = "password", is_admin: bool = False) -> Tuple[models.User, str]:
    user_create_db = schemas.UserCreateDB(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        registration_date=datetime.now(UTC),
        user_age=25, # Default age, adjust if needed
        is_admin=is_admin
    )
    user = user_crud.create_user(db=db, user=user_create_db)
    db.refresh(user) # <-- CRUCIAL FIX: Ensure user object is refreshed and attached
    access_token = create_access_token(data={"sub": user.username})
    return user, access_token

def create_test_game(db: Session, game_name: str = "Test Game", genre: str = "Action", # <-- Added genre
                     release_date: date = date(2023, 1, 1), platform: str = "PC",
                     igdb_id: Optional[int] = None, image_url: Optional[str] = None,
                     age_rating: Optional[str] = None) -> models.Game:
    if igdb_id is None:
        igdb_id = uuid.uuid4().int % (10**9) # Generate a random unique ID

    game_data = schemas.GameCreate(
        game_name=game_name,
        genre=genre, # <-- Pass genre
        release_date=release_date,
        platform=platform,
        igdb_id=igdb_id,
        image_url=image_url,
        age_rating=age_rating
    )
    game = crud.create_game(db=db, game=game_data)
    db.refresh(game) # <-- CRUCIAL FIX: Ensure game object is refreshed and attached
    return game
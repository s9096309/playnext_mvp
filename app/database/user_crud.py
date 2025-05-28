# app/database/user_crud.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc # Needed for sorting in recommendations
from typing import List, Optional
from datetime import datetime, UTC # Import UTC for the deprecation fix

from . import models, schemas # Assuming models and schemas are in the same parent directory


def get_user(db: Session, user_id: int):
    """Retrieves a user by their user ID."""
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """Retrieves a user by their username."""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Retrieves a user by their email address."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreateDB):
    """Creates a new user in the database."""
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        user_age=user.user_age,
        is_admin=user.is_admin, # <-- CRUCIAL FIX: Use the is_admin from the user object!
        registration_date=user.registration_date # Also ensure this uses the one from user object
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Retrieves a list of all users."""
    return db.query(models.User).offset(skip).limit(limit).all()

from app.utils.auth import get_password_hash # You'll need this for password updates

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not db_user:
        return None

    # Get a dictionary of fields from the update schema,
    # but only include those that were explicitly set in the request.
    update_data = user_update.model_dump(exclude_unset=True) # <-- Crucial line!

    for key, value in update_data.items():
        if key == "password": # Handle password hashing if 'password' is in UserUpdate
            setattr(db_user, "password_hash", get_password_hash(value))
        else:
            setattr(db_user, key, value)

    db.add(db_user) # Mark as dirty for update, usually tracked already
    db.commit()
    db.refresh(db_user) # Refresh to get latest state from DB
    return db_user

def delete_user(db: Session, user_id: int):
    """Deletes a user from the database."""
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user # Returns the deleted user object, or None if not found

def get_user_backlog(db: Session, user_id: int) -> List[models.BacklogItem]:
    """Retrieves all backlog items for a specific user."""
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """Retrieves all ratings made by a specific user."""
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def get_user_recommendations(db: Session, user_id: int, limit: int = 10) -> List[models.Game]:
    """
    Retrieves game recommendations for a specific user based on their ratings and backlog.
    This is a simplified example. Real-world recommendations are more complex.
    """
    user_ratings = db.query(models.Rating).filter(models.Rating.user_id == user_id).order_by(
        desc(models.Rating.rating)).limit(5).all()
    user_backlog = db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

    recommended_games = set()
    seen_game_ids = set(rating.game_id for rating in user_ratings) | set(item.game_id for item in user_backlog)

    for rating in user_ratings:
        game = db.query(models.Game).filter(models.Game.game_id == rating.game_id).first()
        if game and game.genre:
            genres = [g.strip() for g in game.genre.split(',')]
            for genre in genres:
                similar_games = db.query(models.Game).filter(models.Game.genre.like(f"%{genre}%"),
                                                             models.Game.game_id.notin_(seen_game_ids)).limit(
                    3).all()
                for similar_game in similar_games:
                    recommended_games.add(similar_game)
                    seen_game_ids.add(similar_game.game_id)
                    if len(recommended_games) >= limit:
                        return list(recommended_games)[:limit]

    return list(recommended_games)[:limit]
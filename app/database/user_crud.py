# app/database/user_crud.py
import uuid
from typing import List, Optional
from datetime import datetime, timezone # Added timezone import
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from app.utils.auth import get_password_hash
from . import models, schemas


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreateDB) -> models.User:
    """
    Creates a new user in the database.

    Args:
        db (Session): The database session.
        user (schemas.UserCreateDB): The Pydantic schema containing user data
                                      including the hashed password and registration date.

    Returns:
        models.User: The newly created SQLAlchemy User model instance.
    """
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        user_age=user.user_age,
        is_admin=user.is_admin,
        registration_date=user.registration_date,
        igdb_id=user.igdb_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True) # Using model_dump for Pydantic v2

    for key, value in update_data.items():
        if key == "password": # Handle password hashing for updates
            setattr(db_user, "password_hash", get_password_hash(value))
        else:
            setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def get_user_backlog(db: Session, user_id: int) -> List[models.BacklogItem]:
    """Retrieve all backlog items for a specific user."""
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()


def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """Retrieve all ratings by a specific user."""
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()


def get_user_recommendations(db: Session, user_id: int, limit: int = 10) -> List[models.Game]:
    """
    Generates game recommendations for a user based on their ratings and backlog.

    This is a simplified in-DB recommendation logic. For more complex scenarios,
    a dedicated recommendation engine or service might be used.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user for whom to generate recommendations.
        limit (int): The maximum number of recommendations to return.

    Returns:
        List[models.Game]: A list of recommended game model instances.
    """
    user_ratings = db.query(models.Rating).filter(models.Rating.user_id == user_id).order_by(
        desc(models.Rating.rating)).limit(5).all()
    user_backlog = db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

    recommended_games_set = set()
    seen_game_ids = {rating.game_id for rating in user_ratings} | \
                   {item.game_id for item in user_backlog}

    for rating in user_ratings:
        game = db.query(models.Game).filter(models.Game.game_id == rating.game_id).first()
        if game and game.genre:
            genres = [g.strip() for g in game.genre.split(',')]
            for genre in genres:
                similar_games = db.query(models.Game).filter(
                    models.Game.genre.like(f"%{genre}%"),
                    models.Game.game_id.notin_(seen_game_ids)
                ).limit(3).all()
                for similar_game in similar_games:
                    recommended_games_set.add(similar_game)
                    seen_game_ids.add(similar_game.game_id)
                    if len(recommended_games_set) >= limit:
                        return list(recommended_games_set)[:limit]

    return list(recommended_games_set)[:limit]

def get_rating_by_user_and_game(db: Session, user_id: uuid.UUID, game_id: int):
    """
    Retrieves a single rating by user_id and game_id.
    """
    return db.query(models.Rating).filter(
        and_(models.Rating.user_id == user_id, models.Rating.game_id == game_id)
    ).first()

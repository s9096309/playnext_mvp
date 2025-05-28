# app/database/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from . import models, schemas
import requests
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime, date, UTC  # Ensure UTC is imported for datetime handling

load_dotenv()

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")


def get_igdb_access_token():
    """Fetches an IGDB access token."""
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_CLIENT_SECRET}&grant_type=client_credentials"
    response = requests.post(url)
    response.raise_for_status()
    return response.json()["access_token"]


def search_igdb_game(game_name: str):
    """Searches for a game on IGDB by name."""
    access_token = get_igdb_access_token()
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": IGDB_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    data = f'search "{game_name}"; fields name, genres.name, platforms.name, first_release_date, cover.image_id, age_ratings.rating, slug; limit 1;'
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def create_game(db: Session, game: schemas.GameCreate):
    db_game = models.Game(**game.model_dump())  # Use model_dump for Pydantic v2+
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()


def get_game_by_name(db: Session, game_name: str, threshold=85):
    from fuzzywuzzy import fuzz
    games = db.query(models.Game).all()
    best_match = None
    best_ratio = 0

    for game in games:
        ratio = fuzz.token_sort_ratio(game_name, game.game_name)
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = game
    return best_match


def get_games(db: Session, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, genre: Optional[str] = None,
              platform: Optional[str] = None):
    query = db.query(models.Game)
    if genre:
        query = query.filter(
            models.Game.genre.ilike(f"%{genre}%"))  # Use ilike for partial/case-insensitive genre match
    if platform:
        query = query.filter(
            models.Game.platform.ilike(f"%{platform}%"))  # Use ilike for partial/case-insensitive platform match
    if sort_by:
        sort_column = sort_by[1:] if sort_by.startswith("-") else sort_by
        if hasattr(models.Game, sort_column):
            order = desc if sort_by.startswith("-") else asc
            query = query.order_by(order(getattr(models.Game, sort_column)))
    return query.offset(skip).limit(limit).all()


def get_game_by_igdb_id(db: Session, igdb_id: int):
    """Retrieves a game from the database by its IGDB ID."""
    return db.query(models.Game).filter(models.Game.igdb_id == igdb_id).first()


def update_game(db: Session, game_id: int, game_update: schemas.GameUpdate) -> Optional[models.Game]:
    db_game = db.query(models.Game).filter(models.Game.game_id == game_id).first()
    if not db_game:
        return None

    update_data = game_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_game, key, value)

    db.commit()
    db.refresh(db_game)
    return db_game


def delete_game(db: Session, game_id: int) -> Optional[models.Game]:
    db_game = db.query(models.Game).filter(models.Game.game_id == game_id).first()
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game


def create_rating(db: Session, rating: schemas.RatingCreate):
    db_rating = models.Rating(**rating.model_dump())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating


def get_rating(db: Session, rating_id: int):
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()


def get_ratings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rating).offset(skip).limit(limit).all()


def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """Retrieves all ratings made by a specific user."""
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()


def get_ratings_with_comments_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """Retrieves all ratings made by a specific user that have comments (not empty strings)."""
    return db.query(models.Rating).filter(models.Rating.user_id == user_id, models.Rating.comment != '').all()


def update_rating(db: Session, rating_id: int, rating_update: schemas.RatingUpdate) -> Optional[models.Rating]:
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()
    if not db_rating:
        return None

    update_data = rating_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rating, key, value)

    db.commit()
    db.refresh(db_rating)
    return db_rating


def delete_rating(db: Session, rating_id: int) -> Optional[models.Rating]:
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()
    if db_rating:
        db.delete(db_rating)
        db.commit()
    return db_rating


def create_backlog_item(db: Session, backlog_item: schemas.BacklogItemCreate):
    db_backlog_item = models.BacklogItem(**backlog_item.model_dump())
    db.add(db_backlog_item)
    db.commit()
    db.refresh(db_backlog_item)
    return db_backlog_item


def get_backlog_item(db: Session, backlog_id: int):
    return db.query(models.BacklogItem).filter(models.BacklogItem.backlog_id == backlog_id).first()


def get_user_backlog(db: Session, user_id: int) -> List[models.BacklogItem]:
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()


def get_backlog_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BacklogItem).offset(skip).limit(limit).all()


def update_backlog_item(db: Session, backlog_id: int, backlog_item_update: schemas.BacklogItemUpdate) -> Optional[
    models.BacklogItem]:
    db_backlog_item = db.query(models.BacklogItem).filter(models.BacklogItem.backlog_id == backlog_id).first()
    if not db_backlog_item:
        return None

    update_data = backlog_item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_backlog_item, key, value)

    db.commit()
    db.refresh(db_backlog_item)
    return db_backlog_item


def delete_backlog_item(db: Session, backlog_id: int) -> Optional[models.BacklogItem]:
    db_backlog_item = db.query(models.BacklogItem).filter(models.BacklogItem.backlog_id == backlog_id).first()
    if db_backlog_item:
        db.delete(db_backlog_item)
        db.commit()
    return db_backlog_item


def create_recommendation(db: Session, recommendation: schemas.RecommendationCreate) -> models.Recommendation:
    db_reco = models.Recommendation(**recommendation.model_dump())
    db.add(db_reco)
    db.commit()
    db.refresh(db_reco)
    return db_reco


def get_recommendation(db: Session, recommendation_id: int) -> Optional[models.Recommendation]:
    return db.query(models.Recommendation).filter(models.Recommendation.recommendation_id == recommendation_id).first()


def get_recommendations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Recommendation]:
    return db.query(models.Recommendation).offset(skip).limit(limit).all()


def update_recommendation(db: Session, recommendation_id: int, recommendation_update: schemas.RecommendationUpdate) -> \
Optional[models.Recommendation]:
    db_reco = db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id).first()
    if not db_reco:
        return None

    update_data = recommendation_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reco, key, value)

    db.commit()
    db.refresh(db_reco)
    return db_reco


def delete_recommendation(db: Session, recommendation_id: int) -> Optional[models.Recommendation]:
    db_reco = db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id).first()
    if db_reco:
        db.delete(db_reco)
        db.commit()
    return db_reco


def search_games_db(db: Session, query: str, limit: int = 10) -> List[models.Game]:
    """
    Searches the local database for games where the name contains the query.
    Uses a case-insensitive 'like' clause.
    """
    return db.query(models.Game).filter(models.Game.game_name.ilike(f"%{query}%")).limit(limit).all()


def create_game_if_not_exists(db: Session, game: schemas.GameCreate) -> models.Game:
    """
    Creates a game in the database if it doesn't already exist based on IGDB ID.
    """
    db_game = db.query(models.Game).filter(models.Game.igdb_id == game.igdb_id).first()
    if not db_game:
        db_game = models.Game(**game.model_dump())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
    return db_game
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from . import models, schemas
import requests
import os
from dotenv import load_dotenv
from typing import Optional, List

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
    db_game = models.Game(**game.dict())
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

def get_games(db: Session, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, genre: Optional[str] = None, platform: Optional[str] = None):
    query = db.query(models.Game)
    if genre:
        query = query.filter(models.Game.genre == genre)
    if platform:
        query = query.filter(models.Game.platform == platform)
    if sort_by:
        sort_column = sort_by[1:] if sort_by.startswith("-") else sort_by
        if hasattr(models.Game, sort_column):
            order = desc if sort_by.startswith("-") else asc
            query = query.order_by(order(getattr(models.Game, sort_column)))
    return query.offset(skip).limit(limit).all()

def create_rating(db: Session, rating: schemas.RatingCreate):
    db_rating = models.Rating(**rating.dict())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def get_rating(db: Session, rating_id: int):
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()

def get_ratings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rating).offset(skip).limit(limit).all()

def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def get_ratings_with_comments_by_user(db: Session, user_id: int) -> List[models.Rating]:
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def create_backlog_item(db: Session, backlog_item: schemas.BacklogItemCreate):
    db_backlog_item = models.BacklogItem(**backlog_item.dict())
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

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_backlog_items(db: Session, user_id: int) -> List[models.BacklogItem]:
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()
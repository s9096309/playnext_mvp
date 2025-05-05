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

def get_game_by_igdb_id(db: Session, igdb_id: int):
    """Retrieves a game from the database by its IGDB ID."""
    return db.query(models.Game).filter(models.Game.igdb_id == igdb_id).first()

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

def create_user(db: Session, user: schemas.UserCreateDB):
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

def get_user_recommendations(db: Session, user_id: int):

    def get_user_recommendations(db: Session, user_id: int, limit: int = 10):
        """
        Retrieves game recommendations for a specific user.
        This is a simplified example. Real-world recommendations are more complex.
        """
        user_ratings = db.query(models.Rating).filter(models.Rating.user_id == user_id).order_by(
            desc(models.Rating.rating)).limit(5).all()
        user_backlog = db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

        recommended_games = set()
        seen_game_ids = set(rating.game_id for rating in user_ratings) | set(item.game_id for item in user_backlog)

        # Recommend games with similar genres (very basic)
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

        # Add more recommendation logic here based on platforms, etc.

        return list(recommended_games)[:limit]

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
        db_game = models.Game(**game.dict())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
    return db_game
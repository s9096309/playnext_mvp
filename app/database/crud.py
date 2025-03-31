from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from . import models, schemas  # Import your models and schemas
from typing import Optional

# User CRUD Operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# Game CRUD Operations
def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()

def get_game_by_igdb_id(db: Session, igdb_id: int):
    return db.query(models.Game).filter(models.Game.igdb_id == igdb_id).first()

def get_games(db: Session, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, genre: Optional[str] = None, platform: Optional[str] = None):
    query = db.query(models.Game)

    if genre:
        query = query.filter(models.Game.genre.ilike(f"%{genre}%"))  # Case-insensitive like search
    if platform:
        query = query.filter(models.Game.platform.ilike(f"%{platform}%")) # Case-insensitive like search

    if sort_by:
        sort_direction = asc
        if sort_by.startswith("-"):
            sort_direction = desc
            sort_by = sort_by[1:]

        if hasattr(models.Game, sort_by):
            query = query.order_by(sort_direction(getattr(models.Game, sort_by)))

    return query.offset(skip).limit(limit).all() if query.offset(skip).limit(limit).all() else []

def create_game(db: Session, game: schemas.GameCreate):
    db_game = db.query(models.Game).filter(models.Game.igdb_id == game.igdb_id).first()
    if db_game:
        return db_game # game already exists, return the existing game.
    db_game = models.Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def update_game(db: Session, game_id: int, game_update: schemas.GameUpdate):
    db_game = get_game(db, game_id)
    if db_game:
        for key, value in game_update.dict(exclude_unset=True).items():
            setattr(db_game, key, value)
        db.commit()
        db.refresh(db_game)
    return db_game

def delete_game(db: Session, game_id: int):
    db_game = get_game(db, game_id)
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game

# BacklogItem CRUD Operations
def get_backlog_item(db: Session, backlog_id: int):
    return db.query(models.BacklogItem).filter(models.BacklogItem.backlog_id == backlog_id).first()

def get_backlog_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BacklogItem).offset(skip).limit(limit).all()

def create_backlog_item(db: Session, backlog_item: schemas.BacklogItemCreate):
    db_backlog_item = models.BacklogItem(**backlog_item.dict())
    db.add(db_backlog_item)
    db.commit()
    db.refresh(db_backlog_item)
    return db_backlog_item

def update_backlog_item(db: Session, backlog_id: int, backlog_item_update: schemas.BacklogItemUpdate):
    db_backlog_item = get_backlog_item(db, backlog_id)
    if db_backlog_item:
        for key, value in backlog_item_update.dict(exclude_unset=True).items():
            setattr(db_backlog_item, key, value)
        db.commit()
        db.refresh(db_backlog_item)
    return db_backlog_item

def delete_backlog_item(db: Session, backlog_id: int):
    db_backlog_item = get_backlog_item(db, backlog_id)
    if db_backlog_item:
        db.delete(db_backlog_item)
        db.commit()
    return db_backlog_item

# Recommendation CRUD Operations
def get_recommendation(db: Session, recommendation_id: int):
    return db.query(models.Recommendation).filter(models.Recommendation.recommendation_id == recommendation_id).first()

def get_recommendations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Recommendation).offset(skip).limit(limit).all()

def create_recommendation(db: Session, recommendation: schemas.RecommendationCreate):
    db_recommendation = models.Recommendation(**recommendation.dict())
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation

def update_recommendation(db: Session, recommendation_id: int, recommendation_update: schemas.RecommendationUpdate):
    db_recommendation = get_recommendation(db, recommendation_id)
    if db_recommendation:
        for key, value in recommendation_update.dict(exclude_unset=True).items():
            setattr(db_recommendation, key, value)
        db.commit()
        db.refresh(db_recommendation)
    return db_recommendation

def delete_recommendation(db: Session, recommendation_id: int):
    db_recommendation = get_recommendation(db, recommendation_id)
    if db_recommendation:
        db.delete(db_recommendation)
        db.commit()
    return db_recommendation

# Ratings CRUD Operations (Corrected to use 'Rating' model)
def get_rating(db: Session, rating_id: int):
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()

def get_ratings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rating).offset(skip).limit(limit).all()

def get_game_ratings(db: Session, game_id: int):
    return db.query(models.Rating).filter(models.Rating.game_id == game_id).all()

def create_rating(db: Session, rating: schemas.RatingCreate):
    db_rating = models.Rating(**rating.dict())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def update_rating(db: Session, rating_id: int, rating_update: schemas.RatingUpdate):
    db_rating = get_rating(db, rating_id)
    if db_rating:
        for key, value in rating_update.dict(exclude_unset=True).items():
            setattr(db_rating, key, value)
        db.commit()
        db.refresh(db_rating)
    return db_rating

def delete_rating(db: Session, rating_id: int):
    db_rating = get_rating(db, rating_id)
    if db_rating:
        db.delete(db_rating)
        db.commit()
    return db_rating

# User CRUD Operations (Specific to user relations)
def get_user_backlog(db: Session, user_id: int):
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

def get_user_ratings(db: Session, user_id: int):
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def get_ratings_by_user(db: Session, user_id: int):
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def get_ratings_with_comments_by_user(db: Session, user_id: int):
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()

def get_game_by_name(db: Session, game_name: str):
    return db.query(models.Game).filter(models.Game.game_name == game_name).first()
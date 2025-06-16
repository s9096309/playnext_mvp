import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from . import models, schemas


def create_game(db: Session, game: schemas.GameCreate) -> models.Game:
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game(db: Session, game_id: int) -> Optional[models.Game]:
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()


def get_game_by_name(
    db: Session,
    game_name: str,
    threshold: int = 85
) -> Optional[models.Game]:
    import fuzzywuzzy.fuzz as fuzz_lib

    games = db.query(models.Game).all()
    best_match: Optional[models.Game] = None
    best_ratio: int = 0

    for game in games:
        ratio = fuzz_lib.token_sort_ratio(game_name, game.game_name)
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = game
    return best_match


def get_games(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    genre: Optional[str] = None,
    platform: Optional[str] = None
) -> List[models.Game]:
    query = db.query(models.Game)

    if genre:
        query = query.filter(models.Game.genre.ilike(f"%{genre}%"))
    if platform:
        query = query.filter(models.Game.platform.ilike(f"%{platform}%"))

    if sort_by:
        sort_column = sort_by[1:] if sort_by.startswith("-") else sort_by
        if hasattr(models.Game, sort_column):
            order_direction: Callable = desc if sort_by.startswith("-") else asc
            query = query.order_by(order_direction(getattr(models.Game, sort_column)))

    return query.offset(skip).limit(limit).all()


def get_game_by_igdb_id(db: Session, igdb_id: int) -> Optional[models.Game]:
    return db.query(models.Game).filter(models.Game.igdb_id == igdb_id).first()


def update_game(
    db: Session,
    game_id: int,
    game_update: schemas.GameUpdate
) -> Optional[models.Game]:
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


def create_rating(db: Session, rating: schemas.RatingCreate) -> models.Rating:
    db_rating = models.Rating(**rating.model_dump())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating


def get_rating(db: Session, rating_id: int) -> Optional[models.Rating]:
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()


def get_ratings(db: Session, skip: int = 0, limit: int = 100) -> List[models.Rating]:
    return db.query(models.Rating).offset(skip).limit(limit).all()


def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()


def get_ratings_with_comments_by_user(db: Session, user_id: int) -> List[models.Rating]:
    return db.query(models.Rating).filter(
        models.Rating.user_id == user_id,
        models.Rating.comment != ''
    ).all()


def update_rating(
    db: Session,
    rating_id: int,
    rating_update: schemas.RatingUpdate
) -> Optional[models.Rating]:
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


def create_backlog_entry(
    db: Session,
    backlog_entry: schemas.BacklogItemCreate # Using BacklogItemCreate as per your schemas.py
) -> models.Backlog:
    db_backlog_entry = models.Backlog(**backlog_entry.model_dump()) # Changed to models.Backlog
    db.add(db_backlog_entry)
    db.commit()
    db.refresh(db_backlog_entry)
    return db_backlog_entry


def get_backlog_entry(db: Session, backlog_id: int) -> Optional[models.Backlog]:
    return db.query(models.Backlog).filter( # Changed to models.Backlog
        models.Backlog.backlog_id == backlog_id
    ).first()


def get_user_backlog(db: Session, user_id: int) -> List[models.Backlog]:
    return db.query(models.Backlog).filter(
        models.Backlog.user_id == user_id
    ).all()


def get_backlog_entries(db: Session, skip: int = 0, limit: int = 100) -> List[models.Backlog]:
    return db.query(models.Backlog).offset(skip).limit(limit).all() # Changed to models.Backlog


def update_backlog_entry(
    db: Session,
    backlog_id: int,
    backlog_update: schemas.BacklogItemUpdate # Using BacklogItemUpdate as per your schemas.py
) -> Optional[models.Backlog]:
    db_backlog_entry = db.query(models.Backlog).filter( # Changed to models.Backlog
        models.Backlog.backlog_id == backlog_id
    ).first()
    if not db_backlog_entry:
        return None

    update_data = backlog_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_backlog_entry, key, value)

    db.commit()
    db.refresh(db_backlog_entry)
    return db_backlog_entry


def delete_backlog_entry(db: Session, backlog_id: int) -> Optional[models.Backlog]:
    db_backlog_entry = db.query(models.Backlog).filter( # Changed to models.Backlog
        models.Backlog.backlog_id == backlog_id
    ).first()
    if db_backlog_entry:
        db.delete(db_backlog_entry)
        db.commit()
    return db_backlog_entry


def create_recommendation(
    db: Session,
    recommendation: schemas.RecommendationCreate
) -> models.Recommendation:
    db_reco = models.Recommendation(**recommendation.model_dump())
    db.add(db_reco)
    db.commit()
    db.refresh(db_reco)
    return db_reco


def get_recommendation(db: Session, recommendation_id: int) -> Optional[models.Recommendation]:
    return db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id
    ).first()


def get_recommendations(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Recommendation]:
    return db.query(models.Recommendation).offset(skip).limit(limit).all()


def get_latest_user_recommendation(db: Session, user_id: int) -> Optional[models.Recommendation]:
    return db.query(models.Recommendation)\
             .filter(models.Recommendation.user_id == user_id)\
             .order_by(models.Recommendation.timestamp.desc())\
             .first()


def update_recommendation(
    db: Session,
    recommendation_id: int,
    recommendation_update: schemas.RecommendationUpdate
) -> Optional[models.Recommendation]:
    db_reco = db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id
    ).first()
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
        models.Recommendation.recommendation_id == recommendation_id
    ).first()
    if db_reco:
        db.delete(db_reco)
        db.commit()
    return db_reco


def search_games_db(db: Session, query: str, limit: int = 10) -> List[models.Game]:
    return db.query(models.Game).filter(
        models.Game.game_name.ilike(f"%{query}%")
    ).limit(limit).all()


def create_game_if_not_exists(db: Session, game: schemas.GameCreate) -> models.Game:
    db_game = db.query(models.Game).filter(models.Game.igdb_id == game.igdb_id).first()
    if not db_game:
        db_game = models.Game(**game.model_dump())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
    return db_game
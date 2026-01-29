"""
Database CRUD (Create, Read, Update, Delete) operations for the PlayNext application.

This module provides functions to interact with the database models
(Game, Rating, Backlog, Recommendation) using SQLAlchemy ORM.
"""

from typing import Callable, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

import fuzzywuzzy.fuzz as fuzz_lib

from . import models, schemas


def create_game(db: Session, game: schemas.GameCreate) -> models.Game:
    """
    Creates a new game record in the database.

    Args:
        db (Session): The database session.
        game (schemas.GameCreate): The Pydantic schema for the game to create.

    Returns:
        models.Game: The newly created game database model.
    """
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game(db: Session, game_id: int) -> Optional[models.Game]:
    """
    Retrieves a single game by its internal database ID.

    Args:
        db (Session): The database session.
        game_id (int): The internal ID of the game.

    Returns:
        Optional[models.Game]: The game database model if found, else None.
    """
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()


def get_game_by_name(
    db: Session,
    game_name: str,
    threshold: int = 85
) -> Optional[models.Game]:
    """
    Searches for a game by name using fuzzy matching.

    Args:
        db (Session): The database session.
        game_name (str): The name of the game to search for.
        threshold (int): The fuzzy matching threshold (0-100).

    Returns:
        Optional[models.Game]: The best matching game database model if found, else None.
    """
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
    """
    Retrieves a list of games with optional filtering, sorting, and pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.
        sort_by (Optional[str]): Field to sort by (e.g., 'game_name', '-release_date').
                                  Prefix with '-' for descending order.
        genre (Optional[str]): Filter games by genre (case-insensitive contains).
        platform (Optional[str]): Filter games by platform (case-insensitive contains).

    Returns:
        List[models.Game]: A list of game database models.
    """
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
    """
    Retrieves a game by its IGDB ID.

    Args:
        db (Session): The database session.
        igdb_id (int): The IGDB ID of the game.

    Returns:
        Optional[models.Game]: The game database model if found, else None.
    """
    return db.query(models.Game).filter(models.Game.igdb_id == igdb_id).first()


def update_game(
    db: Session,
    game_id: int,
    game_update: schemas.GameUpdate
) -> Optional[models.Game]:
    """
    Updates an existing game record in the database.

    Args:
        db (Session): The database session.
        game_id (int): The internal ID of the game to update.
        game_update (schemas.GameUpdate): The Pydantic schema with updated game data.

    Returns:
        Optional[models.Game]: The updated game database model if found, else None.
    """
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
    """
    Deletes a game record from the database.

    Args:
        db (Session): The database session.
        game_id (int): The internal ID of the game to delete.

    Returns:
        Optional[models.Game]: The deleted game database model if it was found and deleted, else None.
    """
    db_game = db.query(models.Game).filter(models.Game.game_id == game_id).first()
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game


def create_rating(db: Session, rating: schemas.RatingCreate) -> models.Rating:
    """
    Creates a new rating record in the database.

    Args:
        db (Session): The database session.
        rating (schemas.RatingCreate): The Pydantic schema for the rating to create.

    Returns:
        models.Rating: The newly created rating database model.
    """
    db_rating = models.Rating(**rating.model_dump())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating


def get_rating(db: Session, rating_id: int) -> Optional[models.Rating]:
    """
    Retrieves a single rating by its internal database ID.

    Args:
        db (Session): The database session.
        rating_id (int): The internal ID of the rating.

    Returns:
        Optional[models.Rating]: The rating database model if found, else None.
    """
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()


def get_ratings(db: Session, skip: int = 0, limit: int = 100) -> List[models.Rating]:
    """
    Retrieves a list of ratings with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Rating]: A list of rating database models.
    """
    return db.query(models.Rating).offset(skip).limit(limit).all()


def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """
    Retrieves all ratings associated with a specific user ID.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[models.Rating]: A list of rating database models for the user.
    """
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()


def get_ratings_with_comments_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """
    Retrieves all ratings with a non-empty comment for a specific user ID.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[models.Rating]: A list of rating database models with comments for the user.
    """
    return db.query(models.Rating).filter(
        models.Rating.user_id == user_id,
        models.Rating.comment != ''
    ).all()


def update_rating(
    db: Session,
    rating_id: int,
    rating_update: schemas.RatingUpdate
) -> Optional[models.Rating]:
    """
    Updates an existing rating record in the database.

    Args:
        db (Session): The database session.
        rating_id (int): The internal ID of the rating to update.
        rating_update (schemas.RatingUpdate): The Pydantic schema with updated rating data.

    Returns:
        Optional[models.Rating]: The updated rating database model if found, else None.
    """
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
    """
    Deletes a rating record from the database.

    Args:
        db (Session): The database session.
        rating_id (int): The internal ID of the rating to delete.

    Returns:
        Optional[models.Rating]: The deleted rating database model if it was found and deleted, else None.
    """
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()
    if db_rating:
        db.delete(db_rating)
        db.commit()
    return db_rating


def create_backlog_entry(
    db: Session,
    backlog_entry: schemas.BacklogItemCreate
) -> models.Backlog:
    """
    Creates a new backlog entry record in the database.

    Args:
        db (Session): The database session.
        backlog_entry (schemas.BacklogItemCreate): The Pydantic schema for the backlog entry to create.

    Returns:
        models.Backlog: The newly created backlog entry database model.
    """
    db_backlog_entry = models.Backlog(**backlog_entry.model_dump())
    db.add(db_backlog_entry)
    db.commit()
    db.refresh(db_backlog_entry)
    return db_backlog_entry


def get_backlog_entry(db: Session, backlog_id: int) -> Optional[models.Backlog]:
    """
    Retrieves a single backlog entry by its internal database ID.

    Args:
        db (Session): The database session.
        backlog_id (int): The internal ID of the backlog entry.

    Returns:
        Optional[models.Backlog]: The backlog entry database model if found, else None.
    """
    return db.query(models.Backlog).filter(
        models.Backlog.backlog_id == backlog_id
    ).first()


def get_user_backlog(db: Session, user_id: int) -> List[models.Backlog]:
    """
    Retrieves all backlog entries for a specific user ID.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        List[models.Backlog]: A list of backlog entry database models for the user.
    """
    return db.query(models.Backlog).filter(
        models.Backlog.user_id == user_id
    ).all()


def get_backlog_entries(db: Session, skip: int = 0, limit: int = 100) -> List[models.Backlog]:
    """
    Retrieves a list of backlog entries with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Backlog]: A list of backlog entry database models.
    """
    return db.query(models.Backlog).offset(skip).limit(limit).all()


def update_backlog_entry(
    db: Session,
    backlog_id: int,
    backlog_update: schemas.BacklogItemUpdate
) -> Optional[models.Backlog]:
    """
    Updates an existing backlog entry record in the database.

    Args:
        db (Session): The database session.
        backlog_id (int): The internal ID of the backlog entry to update.
        backlog_update (schemas.BacklogItemUpdate): The Pydantic schema with updated backlog data.

    Returns:
        Optional[models.Backlog]: The updated backlog entry database model if found, else None.
    """
    db_backlog_entry = db.query(models.Backlog).filter(
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
    """
    Deletes a backlog entry record from the database.

    Args:
        db (Session): The database session.
        backlog_id (int): The internal ID of the backlog entry to delete.

    Returns:
        Optional[models.Backlog]: The deleted backlog entry database model if it was found and deleted, else None.
    """
    db_backlog_entry = db.query(models.Backlog).filter(
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
    """
    Creates a new recommendation record in the database.

    Args:
        db (Session): The database session.
        recommendation (schemas.RecommendationCreate): The Pydantic schema for the recommendation to create.

    Returns:
        models.Recommendation: The newly created recommendation database model.
    """
    db_reco = models.Recommendation(**recommendation.model_dump())
    db.add(db_reco)
    db.commit()
    db.refresh(db_reco)
    return db_reco


def get_recommendation(db: Session, recommendation_id: int) -> Optional[models.Recommendation]:
    """
    Retrieves a single recommendation by its internal database ID.

    Args:
        db (Session): The database session.
        recommendation_id (int): The internal ID of the recommendation.

    Returns:
        Optional[models.Recommendation]: The recommendation database model if found, else None.
    """
    return db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id
    ).first()


def get_recommendations(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Recommendation]:
    """
    Retrieves a list of recommendations with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Recommendation]: A list of recommendation database models.
    """
    return db.query(models.Recommendation).offset(skip).limit(limit).all()


def get_latest_user_recommendation(db: Session, user_id: int) -> Optional[models.Recommendation]:
    """
    Retrieves the latest recommendation for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        Optional[models.Recommendation]: The latest recommendation database model if found, else None.
    """
    return db.query(models.Recommendation)\
             .filter(models.Recommendation.user_id == user_id)\
             .order_by(models.Recommendation.timestamp.desc())\
             .first()


def update_recommendation(
    db: Session,
    recommendation_id: int,
    recommendation_update: schemas.RecommendationUpdate
) -> Optional[models.Recommendation]:
    """
    Updates an existing recommendation record in the database.

    Args:
        db (Session): The database session.
        recommendation_id (int): The internal ID of the recommendation to update.
        recommendation_update (schemas.RecommendationUpdate): The Pydantic schema with updated recommendation data.

    Returns:
        Optional[models.Recommendation]: The updated recommendation database model if found, else None.
    """
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
    """
    Deletes a recommendation record from the database.

    Args:
        db (Session): The database session.
        recommendation_id (int): The internal ID of the recommendation to delete.

    Returns:
        Optional[models.Recommendation]: The deleted recommendation database model if it was found and deleted, else None.
    """
    db_reco = db.query(models.Recommendation).filter(
        models.Recommendation.recommendation_id == recommendation_id
    ).first()
    if db_reco:
        db.delete(db_reco)
        db.commit()
    return db_reco


def search_games_db(db: Session, query: str, limit: int = 10) -> List[models.Game]:
    """
    Searches for games in the database by name using a case-insensitive 'like' query.

    Args:
        db (Session): The database session.
        query (str): The search string for game names.
        limit (int): The maximum number of results to return.

    Returns:
        List[models.Game]: A list of matching game database models.
    """
    return db.query(models.Game).filter(
        models.Game.game_name.ilike(f"%{query}%")
    ).limit(limit).all()


def create_game_if_not_exists(db: Session, game: schemas.GameCreate) -> models.Game:
    """
    Creates a game record in the database if it doesn't already exist based on IGDB ID.

    Args:
        db (Session): The database session.
        game (schemas.GameCreate): The Pydantic schema for the game to create.

    Returns:
        models.Game: The existing or newly created game database model.
    """
    db_game = db.query(models.Game).filter(models.Game.igdb_id == game.igdb_id).first()
    if not db_game:
        db_game = models.Game(**game.model_dump())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
    return db_game
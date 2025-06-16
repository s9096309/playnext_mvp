# app/database/crud.py

"""
CRUD operations for PlayNext database models.

This module provides functions for creating, reading, updating, and deleting
records for games, ratings, backlog items, and recommendations.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from . import models, schemas


def create_game(db: Session, game: schemas.GameCreate) -> models.Game:
    """
    Creates a new game record in the database.

    Args:
        db (Session): The database session.
        game (schemas.GameCreate): The Pydantic schema containing game data.

    Returns:
        models.Game: The newly created game database object.
    """
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game(db: Session, game_id: int) -> Optional[models.Game]:
    """
    Retrieves a game record by its ID.

    Args:
        db (Session): The database session.
        game_id (int): The ID of the game to retrieve.

    Returns:
        Optional[models.Game]: The game object if found, otherwise None.
    """
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()


def get_game_by_name(
    db: Session,
    game_name: str,
    threshold: int = 85
) -> Optional[models.Game]:
    """
    Retrieves a game record by name, using fuzzy matching.

    Args:
        db (Session): The database session.
        game_name (str): The name of the game to search for.
        threshold (int): The fuzzy matching threshold (0-100).

    Returns:
        Optional[models.Game]: The best matching game object if found above
                                the threshold, otherwise None.
    """
    import fuzzywuzzy.fuzz as fuzz_lib # Temporarily re-import for this function

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
    Retrieves a list of game records with optional filtering and sorting.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip (for pagination).
        limit (int): The maximum number of records to return.
        sort_by (Optional[str]): Field to sort by, optionally prefixed with '-' for descending.
                                  E.g., "game_name", "-release_date".
        genre (Optional[str]): Filter games by genre (case-insensitive partial match).
        platform (Optional[str]): Filter games by platform (case-insensitive partial match).

    Returns:
        List[models.Game]: A list of game objects.
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
    Retrieves a game record by its IGDB ID.

    Args:
        db (Session): The database session.
        igdb_id (int): The IGDB ID of the game to retrieve.

    Returns:
        Optional[models.Game]: The game object if found, otherwise None.
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
        game_id (int): The ID of the game to update.
        game_update (schemas.GameUpdate): The Pydantic schema with update data.

    Returns:
        Optional[models.Game]: The updated game object if found, otherwise None.
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
        game_id (int): The ID of the game to delete.

    Returns:
        Optional[models.Game]: The deleted game object if found and deleted,
                                otherwise None.
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
        rating (schemas.RatingCreate): The Pydantic schema containing rating data.

    Returns:
        models.Rating: The newly created rating database object.
    """
    db_rating = models.Rating(**rating.model_dump())
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating


def get_rating(db: Session, rating_id: int) -> Optional[models.Rating]:
    """
    Retrieves a rating record by its ID.

    Args:
        db (Session): The database session.
        rating_id (int): The ID of the rating to retrieve.

    Returns:
        Optional[models.Rating]: The rating object if found, otherwise None.
    """
    return db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()


def get_ratings(db: Session, skip: int = 0, limit: int = 100) -> List[models.Rating]:
    """
    Retrieves a list of rating records with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Rating]: A list of rating objects.
    """
    return db.query(models.Rating).offset(skip).limit(limit).all()


def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """
    Retrieves all rating records for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user whose ratings to retrieve.

    Returns:
        List[models.Rating]: A list of rating objects for the specified user.
    """
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()


def get_ratings_with_comments_by_user(db: Session, user_id: int) -> List[models.Rating]:
    """
    Retrieves rating records with comments for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user whose ratings to retrieve.

    Returns:
        List[models.Rating]: A list of rating objects with comments for the user.
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
        rating_id (int): The ID of the rating to update.
        rating_update (schemas.RatingUpdate): The Pydantic schema with update data.

    Returns:
        Optional[models.Rating]: The updated rating object if found, otherwise None.
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
        rating_id (int): The ID of the rating to delete.

    Returns:
        Optional[models.Rating]: The deleted rating object if found and deleted,
                                otherwise None.
    """
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()
    if db_rating:
        db.delete(db_rating)
        db.commit()
    return db_rating


def create_backlog_entry( # Renamed function
    db: Session,
    backlog_entry: schemas.BacklogCreate # Changed schema to BacklogCreate
) -> models.Backlog: # Changed return type to models.Backlog
    """
    Creates a new backlog entry record in the database.

    Args:
        db (Session): The database session.
        backlog_entry (schemas.BacklogCreate): The Pydantic schema containing
                                                backlog entry data.

    Returns:
        models.Backlog: The newly created backlog database object.
    """
    db_backlog_entry = models.Backlog(**backlog_entry.model_dump()) # Changed to models.Backlog
    db.add(db_backlog_entry)
    db.commit()
    db.refresh(db_backlog_entry)
    return db_backlog_entry


def get_backlog_entry(db: Session, backlog_id: int) -> Optional[models.Backlog]: # Renamed function, changed return type
    """
    Retrieves a backlog entry record by its ID.

    Args:
        db (Session): The database session.
        backlog_id (int): The ID of the backlog entry to retrieve.

    Returns:
        Optional[models.Backlog]: The backlog entry object if found,
                                      otherwise None.
    """
    return db.query(models.Backlog).filter( # Changed to models.Backlog
        models.Backlog.backlog_id == backlog_id
    ).first()


def get_user_backlog(db: Session, user_id: int) -> List[models.Backlog]: # Return type already correct
    """
    Retrieves all backlog entries for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user whose backlog to retrieve.

    Returns:
        List[models.Backlog]: A list of backlog entry objects for the user.
    """
    return db.query(models.Backlog).filter(
        models.Backlog.user_id == user_id
    ).all()


def get_backlog_entries(db: Session, skip: int = 0, limit: int = 100) -> List[models.Backlog]: # Renamed function, changed return type
    """
    Retrieves a list of backlog entries with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Backlog]: A list of backlog entry objects.
    """
    return db.query(models.Backlog).offset(skip).limit(limit).all() # Changed to models.Backlog


def update_backlog_entry( # Renamed function
    db: Session,
    backlog_id: int,
    backlog_update: schemas.BacklogUpdate # Changed schema to BacklogUpdate
) -> Optional[models.Backlog]: # Changed return type to models.Backlog
    """
    Updates an existing backlog entry record in the database.

    Args:
        db (Session): The database session.
        backlog_id (int): The ID of the backlog entry to update.
        backlog_update (schemas.BacklogUpdate): The Pydantic schema with
                                                         update data.

    Returns:
        Optional[models.Backlog]: The updated backlog entry object if found,
                                      otherwise None.
    """
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


def delete_backlog_entry(db: Session, backlog_id: int) -> Optional[models.Backlog]: # Renamed function, changed return type
    """
    Deletes a backlog entry record from the database.

    Args:
        db (Session): The database session.
        backlog_id (int): The ID of the backlog entry to delete.

    Returns:
        Optional[models.Backlog]: The deleted backlog entry object if found
                                      and deleted, otherwise None.
    """
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
    """
    Creates a new recommendation record in the database.
    This now stores the full Gemini response.

    Args:
        db (Session): The database session.
        recommendation (schemas.RecommendationCreate): The Pydantic schema
                                                     containing recommendation data.

    Returns:
        models.Recommendation: The newly created recommendation database object.
    """
    db_reco = models.Recommendation(**recommendation.model_dump())
    db.add(db_reco)
    db.commit()
    db.refresh(db_reco)
    return db_reco


def get_recommendation(db: Session, recommendation_id: int) -> Optional[models.Recommendation]:
    """
    Retrieves a recommendation record by its ID.

    Args:
        db (Session): The database session.
        recommendation_id (int): The ID of the recommendation to retrieve.

    Returns:
        Optional[models.Recommendation]: The recommendation object if found,
                                         otherwise None.
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
    Retrieves a list of recommendation records with pagination.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[models.Recommendation]: A list of recommendation objects.
    """
    return db.query(models.Recommendation).offset(skip).limit(limit).all()


def get_latest_user_recommendation(db: Session, user_id: int) -> Optional[models.Recommendation]:
    """
    Retrieves the most recent recommendation generated for a user.
    Used for caching purposes.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user.

    Returns:
        Optional[models.Recommendation]: The most recent recommendation object if found,
                                         otherwise None.
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
    This now updates the cached Gemini response.

    Args:
        db (Session): The database session.
        recommendation_id (int): The ID of the recommendation to update.
        recommendation_update (schemas.RecommendationUpdate): The Pydantic schema
                                                             with update data.

    Returns:
        Optional[models.Recommendation]: The updated recommendation object if found,
                                         otherwise None.
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
        recommendation_id (int): The ID of the recommendation to delete.

    Returns:
        Optional[models.Recommendation]: The deleted recommendation object if found
                                         and deleted, otherwise None.
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
    Searches for games in the database by name (case-insensitive partial match).

    Args:
        db (Session): The database session.
        query (str): The search query string.
        limit (int): The maximum number of results to return.

    Returns:
        List[models.Game]: A list of matching game objects.
    """
    return db.query(models.Game).filter(
        models.Game.game_name.ilike(f"%{query}%")
    ).limit(limit).all()


def create_game_if_not_exists(db: Session, game: schemas.GameCreate) -> models.Game:
    """
    Creates a new game record if it doesn't already exist based on IGDB ID.

    Args:
        db (Session): The database session.
        game (schemas.GameCreate): The Pydantic schema containing game data.

    Returns:
        models.Game: The existing game object if found, or the newly created game object.
    """
    db_game = db.query(models.Game).filter(models.Game.igdb_id == game.igdb_id).first()
    if not db_game:
        db_game = models.Game(**game.model_dump())
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
    return db_game
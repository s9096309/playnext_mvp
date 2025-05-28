# app/routers/ratings.py

"""
API routes for managing game ratings.

This module provides endpoints for creating, retrieving, updating, and deleting
user-submitted ratings for games. It includes validation and authorization
logic to ensure users can only manage their own ratings.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from app.database import crud, models, schemas
from app.database.session import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=schemas.Rating, status_code=status.HTTP_201_CREATED)
def create_rating(
    rating: schemas.RatingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new rating for a game.

    A user can only create a rating for their own user ID.
    Validates that both the user and the game exist before creating the rating.

    Args:
        rating (schemas.RatingCreate): The rating data to create, including user_id, game_id, and rating.
        current_user (models.User): The authenticated user making the request.
        db (Session): The database session.

    Returns:
        schemas.Rating: The newly created rating object.

    Raises:
        HTTPException:
            - 403 Forbidden: If the user tries to create a rating for another user_id.
            - 404 Not Found: If the specified user or game does not exist.
    """
    if rating.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create rating for another user."
        )

    db_user = crud.get_user(db, user_id=rating.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_game = crud.get_game(db, game_id=rating.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_rating(db=db, rating=rating)


@router.get("/{rating_id}", response_model=schemas.Rating)
def read_rating(
    rating_id: int,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves a single rating by its ID.

    Args:
        rating_id (int): The ID of the rating to retrieve.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        schemas.Rating: The retrieved rating object.

    Raises:
        HTTPException: 404 Not Found: If the rating with the given ID does not exist.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return db_rating


@router.get("/", response_model=List[schemas.Rating])
def read_ratings(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all ratings with pagination.

    Args:
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        List[schemas.Rating]: A list of rating objects.
    """
    ratings = crud.get_ratings(db, skip=skip, limit=limit)
    return ratings


@router.put("/{rating_id}", response_model=schemas.Rating)
def update_rating(
    rating_id: int,
    rating_update: schemas.RatingUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing rating.

    A user can only update their own ratings.
    Validates if the game_id in the update exists if it's provided.

    Args:
        rating_id (int): The ID of the rating to update.
        rating_update (schemas.RatingUpdate): The updated rating data.
        current_user (models.User): The authenticated user making the request.
        db (Session): The database session.

    Returns:
        schemas.Rating: The updated rating object.

    Raises:
        HTTPException:
            - 404 Not Found: If the rating or the associated game (if game_id is updated) is not found.
            - 403 Forbidden: If the user tries to update a rating that does not belong to them.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this rating")

    # If game_id is part of the update, ensure the game exists
    if rating_update.game_id is not None:
        db_game = crud.get_game(db, game_id=rating_update.game_id)
        if not db_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_rating(db=db, rating_id=rating_id, rating_update=rating_update)


@router.delete("/{rating_id}", status_code=status.HTTP_200_OK, response_model=schemas.Rating)
def delete_rating(
    rating_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a rating.

    A user can only delete their own ratings.

    Args:
        rating_id (int): The ID of the rating to delete.
        current_user (models.User): The authenticated user making the request.
        db (Session): The database session.

    Returns:
        schemas.Rating: The deleted rating object.

    Raises:
        HTTPException:
            - 404 Not Found: If the rating is not found.
            - 403 Forbidden: If the user tries to delete a rating that does not belong to them.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this rating")

    return crud.delete_rating(db, rating_id=rating_id)


@router.get("/user/{user_id}", response_model=List[schemas.Rating])
def read_user_ratings(
    user_id: int,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves all ratings submitted by a specific user.

    Args:
        user_id (int): The ID of the user whose ratings to retrieve.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        List[schemas.Rating]: A list of rating objects for the specified user.

    Raises:
        HTTPException: 404 Not Found: If no ratings are found for the user.
    """
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ratings not found for this user")
    return ratings


@router.get("/game/{game_id}", response_model=List[schemas.Rating])
def read_game_ratings(
    game_id: int,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves all ratings for a specific game.

    Args:
        game_id (int): The ID of the game whose ratings to retrieve.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        List[schemas.Rating]: A list of rating objects for the specified game.
    """
    return crud.get_game_ratings(db, game_id=game_id)


@router.options("/")
async def ratings_options(request: Request): # pylint: disable=W0613
    """
    Handles OPTIONS requests for the /ratings/ endpoint.

    This is typically used for CORS preflight requests by web browsers.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        Response: An HTTP 200 OK response with appropriate CORS headers.
    """
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*", # Consider making this more restrictive in production
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })
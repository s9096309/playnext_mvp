# app/routers/backlog_items.py

"""
API routes for managing user game backlog items.

This module provides endpoints for creating, retrieving, updating, and deleting
games within a user's backlog. It includes authorization checks to ensure
users can only manage their own backlog entries.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import crud
from database import schemas, models
from database.session import get_db
from utils.auth import get_current_user



router = APIRouter(prefix="/backlog", tags=["Backlog"])


@router.post("/", response_model=schemas.BacklogItem, status_code=status.HTTP_201_CREATED)
def create_backlog_item(
    backlog_item: schemas.BacklogItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new backlog item for a user.

    A user can only create backlog items associated with their own user ID.
    This endpoint also validates that the specified user and game exist.

    Args:
        backlog_item (schemas.BacklogItemCreate): The data for the new backlog item.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.BacklogItem: The newly created backlog item.

    Raises:
        HTTPException:
            - 403 Forbidden: If attempting to create a backlog item for another user.
            - 404 Not Found: If the specified user or game does not exist.
    """
    if backlog_item.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create backlog item for another user."
        )

    db_user = crud.get_user(db, user_id=backlog_item.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_game = crud.get_game(db, game_id=backlog_item.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_backlog_item(db=db, backlog_item=backlog_item)


@router.get("/{backlog_item_id}", response_model=schemas.BacklogItem)
def read_backlog_item(
    backlog_item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single backlog item by its ID.

    Ensures that the authenticated user is authorized to view this specific item.

    Args:
        backlog_item_id (int): The ID of the backlog item to retrieve.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.BacklogItem: The retrieved backlog item.

    Raises:
        HTTPException:
            - 404 Not Found: If the backlog item does not exist.
            - 403 Forbidden: If the user is not authorized to view the item.
    """
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_item_id)
    if not db_backlog_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")

    if db_backlog_item.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this backlog item."
        )

    return db_backlog_item


@router.get("/", response_model=List[schemas.BacklogItem])
def read_backlog_items(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all backlog items with pagination.

    Note: In a typical application, access to all backlog items might be restricted
    to administrators. This endpoint currently returns all items regardless of user.

    Args:
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        List[schemas.BacklogItem]: A list of backlog items.
    """
    backlog_items = crud.get_user_backlog(db, user_id=current_user.user_id)
    return backlog_items[skip : skip + limit]


@router.put("/{backlog_item_id}", response_model=schemas.BacklogItem)
def update_backlog_item(
    backlog_item_id: int,
    backlog_item_update: schemas.BacklogItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing backlog item.

    A user can only update their own backlog items. Validates if the game_id
    in the update payload exists if it's provided.

    Args:
        backlog_item_id (int): The ID of the backlog item to update.
        backlog_item_update (schemas.BacklogItemUpdate): The updated backlog item data.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.BacklogItem: The updated backlog item.

    Raises:
        HTTPException:
            - 404 Not Found: If the backlog item or the associated game (if game_id is updated)
                             is not found.
            - 403 Forbidden: If the user is not authorized to update this item.
    """
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_item_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")

    if db_backlog_item.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this backlog item."
        )

    # If game_id is part of the update, ensure the game exists
    if backlog_item_update.game_id is not None:
        db_game = crud.get_game(db, game_id=backlog_item_update.game_id)
        if not db_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_backlog_item(
        db=db, backlog_id=backlog_item_id, backlog_item_update=backlog_item_update
    )


@router.delete("/{backlog_item_id}", status_code=status.HTTP_200_OK, response_model=schemas.BacklogItem)
def delete_backlog_item(
    backlog_item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a backlog item.

    A user can only delete their own backlog items.

    Args:
        backlog_item_id (int): The ID of the backlog item to delete.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.BacklogItem: The deleted backlog item.

    Raises:
        HTTPException:
            - 404 Not Found: If the backlog item does not exist.
            - 403 Forbidden: If the user is not authorized to delete this item.
    """
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_item_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")

    if db_backlog_item.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this backlog item."
        )

    return crud.delete_backlog_item(db=db, backlog_id=backlog_item_id)


@router.get("/user/{user_id}", response_model=List[schemas.BacklogItem])
def read_user_backlog(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all backlog items for a specific user.

    This endpoint requires authorization to ensure a user can only view their own backlog.

    Args:
        user_id (int): The ID of the user whose backlog to retrieve.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        List[schemas.BacklogItem]: A list of backlog items for the specified user.

    Raises:
        HTTPException: 403 Forbidden: If the user attempts to view another user's backlog.
    """
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's backlog."
        )

    backlog_items = crud.get_user_backlog(db, user_id=user_id)
    return backlog_items
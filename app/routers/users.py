# app/routers/users.py

"""
API routes for user management and profile-related operations.

This module defines endpoints for creating, retrieving, updating, and deleting
user accounts, as well as accessing a user's personal backlog, ratings, and recommendations.
"""

import datetime # Standard library import
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import models, schemas
from app.database.session import get_db
from app.database import user_crud
from app.utils.auth import get_current_user
from app.utils.security import hash_password # Corrected import: Use hash_password


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the system.

    Checks for existing username and email before creating the user.
    Hashes the password and sets the registration date to the current UTC time.

    Args:
        user (schemas.UserCreate): The user data to create.
        db (Session): The database session.

    Returns:
        schemas.User: The created user's data.

    Raises:
        HTTPException: If a user with the provided username or email already exists.
    """
    db_user = user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Use the correct function name: hash_password
    hashed_password = hash_password(user.password)

    user_create_db = schemas.UserCreateDB(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        registration_date=datetime.datetime.now(datetime.UTC),
        user_age=user.user_age,
        is_admin=user.is_admin, # Keep this from UserCreate or explicitly set it
        igdb_id=user.igdb_id # Pass igdb_id from UserCreate
    )
    return user_crud.create_user(db=db, user=user_create_db)


@router.get("/me", response_model=schemas.User)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """
    Retrieves the details of the currently authenticated user.

    Args:
        current_user (models.User): The authenticated user obtained from the dependency.

    Returns:
        schemas.User: The current user's data.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user), # pylint: disable=W0613
    db: Session = Depends(get_db)
):
    """
    Retrieves a user by their ID.

    Note: In a production application, access to arbitrary user profiles
    might be restricted based on permissions (e.g., only by admin or for the user themselves).
    The `current_user` parameter is present for authentication but not directly
    used for authorization in this specific endpoint, thus it's marked with `# pylint: disable=W0613`.

    Args:
        user_id (int): The ID of the user to retrieve.
        current_user (models.User): The authenticated user (for dependency purposes).
        db (Session): The database session.

    Returns:
        schemas.User: The user's data.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all users.

    This endpoint requires administrative privileges.

    Args:
        skip (int): The number of records to skip (for pagination).
        limit (int): The maximum number of records to return.
        current_user (models.User): The authenticated user. Used for authorization.
        db (Session): The database session.

    Returns:
        List[schemas.User]: A list of user objects.

    Raises:
        HTTPException: If the current user is not authorized (not an admin).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to read all users."
        )
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate, # Renamed parameter for clarity
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates details for an existing user.

    A user can only update their own profile unless they have administrator privileges.

    Args:
        user_id (int): The ID of the user to update.
        user_update (schemas.UserUpdate): The user data for the update.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.User: The updated user's data.

    Raises:
        HTTPException: If the user is not found or the current user is not authorized.
    """
    if user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    db_user = user_crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a user from the system.

    A user can only delete their own account unless they have administrator privileges.

    Args:
        user_id (int): The ID of the user to delete.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.User: The deleted user's data.

    Raises:
        HTTPException: If the user is not found or the current user is not authorized.
    """
    if user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )

    db_user = user_crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.put("/me", response_model=schemas.User)
def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the profile of the currently authenticated user.

    Args:
        user_update (schemas.UserUpdate): The user data for the update.
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.User: The updated user's data.
    """
    return user_crud.update_user(db=db, user_id=current_user.user_id, user_update=user_update)


@router.delete("/me", response_model=schemas.User)
def delete_current_user(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes the account of the currently authenticated user.

    Args:
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        schemas.User: The deleted user's data.
    """
    user_crud.delete_user(db, user_id=current_user.user_id)
    return current_user


@router.get("/me/backlog", response_model=List[schemas.BacklogItem])
def read_users_me_backlog(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the backlog items for the currently authenticated user.

    Args:
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        List[schemas.BacklogItem]: A list of backlog items for the user.
    """
    backlog_items = user_crud.get_user_backlog(db, user_id=current_user.user_id)
    return backlog_items


@router.get("/me/ratings", response_model=List[schemas.Rating])
def read_users_me_ratings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the game ratings submitted by the currently authenticated user.

    Args:
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        List[schemas.Rating]: A list of game rating objects for the user.
    """
    ratings = user_crud.get_ratings_by_user(db, user_id=current_user.user_id)
    return ratings


@router.get("/me/recommendations", response_model=List[schemas.Game]) # Changed response_model to List[schemas.Game]
async def read_users_me_recommendations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves game recommendations for the currently authenticated user.

    Args:
        current_user (models.User): The currently authenticated user.
        db (Session): The database session.

    Returns:
        List[schemas.Game]: A list of recommended game objects for the user.
    """
    # Directly call user_crud.get_user_recommendations as it exists in user_crud.py
    return user_crud.get_user_recommendations(db=db, user_id=current_user.user_id)
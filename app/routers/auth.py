# app/routers/auth.py

"""
API routes for user authentication.

This module handles user login and the generation of access tokens
using OAuth2 password flow.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import schemas, user_crud
from app.database.session import get_db
from app.utils.auth import create_access_token
from app.utils.security import verify_password


ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticates a user and generates an access token upon successful login.

    This endpoint takes a username and password via OAuth2PasswordRequestForm.
    It verifies the credentials against the database and, if valid, issues a JWT
    access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the
                                               username and password.
        db (Session): The database session dependency.

    Returns:
        schemas.Token: An object containing the access token and its type ("bearer").

    Raises:
        HTTPException:
            - 400 Bad Request: If the username or password is incorrect.
    """
    user = user_crud.get_user_by_username(db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
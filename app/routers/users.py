import datetime
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import joinedload, selectinload
from starlette.responses import Response

from app.database import models, schemas
from app.database import user_crud
from app.routers.recommendations import get_user_recommendations as get_recs_from_service

from app.utils.auth import get_current_user, get_current_active_user
from app.utils.security import hash_password
from app.database.session import SessionDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: SessionDep):
    """
    Registers a new user in the system.

    Checks for existing username and email before creating the user.
    Hashes the password and sets the registration date to the current UTC time.
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

    hashed_password = hash_password(user.password)

    registration_date_naive = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    user_create_db = schemas.UserCreateDB(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        registration_date=registration_date_naive,
        user_age=user.user_age,
        is_admin=user.is_admin,
        igdb_id=user.igdb_id
    )
    return user_crud.create_user(db=db, user=user_create_db)


@router.get("/", response_model=List[schemas.User])
def read_users(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieves a list of all users. Accessible only by administrators.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all users."
        )
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=schemas.User)
def read_current_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    """
    Retrieves the details of the currently authenticated user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Retrieves a user by their ID.
    """
    db_user = user_crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Updates details for an existing user.

    A user can only update their own profile unless they have administrator privileges.
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
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Deletes a user from the system.

    A user can only delete their own account unless they have administrator privileges.
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
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Updates the profile of the currently authenticated user.
    """
    return user_crud.update_user(db=db, user_id=current_user.user_id,
                                 user_update=user_update)


@router.delete("/me", response_model=schemas.User)
def delete_current_user(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Deletes the account of the currently authenticated user.
    """
    user_crud.delete_user(db, user_id=current_user.user_id)
    return current_user


@router.post("/me/ratings/", response_model=schemas.RatingResponse)
def create_my_rating(
    rating_data: schemas.RatingCreateMe,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    game = db.query(models.Game).filter(models.Game.game_id == rating_data.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")

    existing_rating = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.user_id,
        models.Rating.game_id == rating_data.game_id
    ).first()

    if existing_rating:
        raise HTTPException(status_code=409, detail="You have already rated this game. Please use the PUT method to update it.")

    current_utc_naive = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    db_rating = models.Rating(
        user_id=current_user.user_id,
        game_id=rating_data.game_id,
        rating=rating_data.rating,
        comment=rating_data.comment,
        rating_date=rating_data.rating_date.replace(tzinfo=None) if rating_data.rating_date else current_utc_naive
    )

    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)

    db_rating_with_game = db.query(models.Rating).options(
        selectinload(models.Rating.game)
    ).filter(models.Rating.rating_id == db_rating.rating_id).first()

    if not db_rating_with_game:
        raise HTTPException(status_code=500, detail="Failed to retrieve created rating with game data.")

    return db_rating_with_game


@router.get("/me/ratings", response_model=List[schemas.RatingResponse])
def read_users_me_ratings(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Retrieves the game ratings submitted by the currently authenticated user.
    Includes game details for display.
    """
    ratings_with_games = (
        db.query(models.Rating)
        .filter(models.Rating.user_id == current_user.user_id)
        .options(joinedload(models.Rating.game))
        .all()
    )
    return ratings_with_games


@router.get("/me/ratings/{rating_id}", response_model=schemas.RatingResponse)
def read_my_rating_by_id(
    rating_id: int,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """
    Retrieves a specific game rating submitted by the currently authenticated user.
    """
    db_rating = db.query(models.Rating).options(
        selectinload(models.Rating.game)
    ).filter(models.Rating.rating_id == rating_id).first()

    if not db_rating:
        raise HTTPException(status_code=404, detail="Rating not found.")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this rating.")

    return db_rating


@router.put("/me/ratings/{rating_id}", response_model=schemas.RatingResponse)
def update_my_rating(
        rating_id: int,
        rating_update: schemas.RatingUpdate,
        current_user: Annotated[models.User, Depends(get_current_active_user)],
        db: SessionDep
):
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()

    if not db_rating:
        raise HTTPException(status_code=404, detail="Rating not found.")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this rating.")

    update_data = rating_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_rating, key, value)

    db_rating.updated_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)

    db_rating_with_game = db.query(models.Rating).options(
        selectinload(models.Rating.game)
    ).filter(models.Rating.rating_id == db_rating.rating_id).first()

    if not db_rating_with_game:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated rating with game data.")

    return db_rating_with_game


@router.delete("/me/ratings/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_rating(
    rating_id: int,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()

    if not db_rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found."
        )

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this rating."
        )

    db.delete(db_rating)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/backlog", response_model=List[schemas.BacklogItem])
def read_users_me_backlog(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    """
    Retrieves the backlog items for the currently authenticated user.
    """
    backlog_items = user_crud.get_user_backlog(db, user_id=current_user.user_id)
    return backlog_items


@router.get(
    "/me/recommendations",
    response_model=schemas.RecommendationResponse,
    summary="Get recommendations for the current user",
    description="Retrieves personalized game recommendations for the authenticated user, "
                "prioritizing cached recommendations if available and not expired. "
                "Can force new generation if needed.",
)
async def read_users_me_recommendations(
    db: SessionDep,
    current_user: Annotated[models.User, Depends(get_current_user)],
    force_generate: bool = Query(
        False,
        description="Set to true to force new recommendations generation, bypassing cache."
    )
):
    """
    This endpoint now calls the get_user_recommendations from the recommendations router,
    passing through the user_id and force_generate flag.
    """
    return await get_recs_from_service(user_id=current_user.user_id, db=db, force_generate=force_generate)
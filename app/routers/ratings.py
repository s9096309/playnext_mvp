import datetime
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import joinedload, selectinload
from starlette.responses import Response

from app.database import models, schemas
from app.database.session import SessionDep
from app.utils.auth import get_current_user, get_current_active_user


router = APIRouter(tags=["Ratings"])


@router.post("/", response_model=schemas.RatingResponse, status_code=status.HTTP_200_OK)
def create_my_rating(
    rating_data: schemas.RatingCreateMe,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    game = db.query(models.Game).filter(models.Game.game_id == rating_data.game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")

    existing_rating = db.query(models.Rating).filter(
        models.Rating.user_id == current_user.user_id,
        models.Rating.game_id == rating_data.game_id
    ).first()

    if existing_rating:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="You have already rated this game. Please use the PUT method to update it.")

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve created rating with game data.")

    return db_rating_with_game


@router.get("/", response_model=List[schemas.RatingResponse])
def read_my_ratings(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: SessionDep
):
    ratings_with_games = (
        db.query(models.Rating)
        .filter(models.Rating.user_id == current_user.user_id)
        .options(joinedload(models.Rating.game))
        .all()
    )
    return ratings_with_games


@router.get("/{rating_id}", response_model=schemas.RatingResponse)
def read_my_rating_by_id(
    rating_id: int,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    db_rating = db.query(models.Rating).options(
        selectinload(models.Rating.game)
    ).filter(models.Rating.rating_id == rating_id).first()

    if not db_rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found.")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this rating.")

    return db_rating


@router.put("/{rating_id}", response_model=schemas.RatingResponse)
def update_my_rating(
    rating_id: int,
    rating_update: schemas.RatingUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    db_rating = db.query(models.Rating).filter(models.Rating.rating_id == rating_id).first()

    if not db_rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found.")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this rating.")

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to retrieve updated rating with game data.")

    return db_rating_with_game


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
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
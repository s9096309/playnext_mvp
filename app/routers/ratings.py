# app/routers/ratings.py

import datetime
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import joinedload, selectinload
from starlette.responses import Response

from app.database import crud, models, schemas # Make sure crud is imported and contains rating operations
from app.database.session import SessionDep, get_db, Session
from app.utils.auth import get_current_user, get_current_active_user # Needed for authenticated endpoints

# Ensure the APIRouter has NO prefix here! The prefix is added in main.py
router = APIRouter(tags=["Ratings"]) # Removed 'prefix="/ratings"'


# --- General Rating Endpoints (if you want these) ---
# These are the ones you had commented out, uncommented and adjusted if needed.

@router.post("/", response_model=schemas.RatingResponse, status_code=status.HTTP_201_CREATED)
def create_rating_general(rating: schemas.RatingCreate, db: Session = Depends(get_db)): # Renamed for clarity
    """Admin or general endpoint to create a rating (consider if this needs current_user check)"""
    # You might want to add a current_user check here for who can create general ratings
    return crud.create_rating(db=db, rating=rating) # Make sure crud.create_rating expects schemas.RatingCreate

@router.get("/{rating_id}", response_model=schemas.RatingResponse) # Changed response_model to RatingResponse if that's standard
def read_rating_by_id_general(rating_id: int, db: Session = Depends(get_db)): # Renamed
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return db_rating

@router.get("/", response_model=List[schemas.RatingResponse]) # Changed response_model
def read_all_ratings_general(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): # Renamed
    """Admin endpoint to get all ratings. Consider adding current_user check."""
    ratings = crud.get_ratings(db, skip=skip, limit=limit)
    return ratings

@router.put("/{rating_id}", response_model=schemas.RatingResponse)
def update_rating_general(rating_id: int, rating: schemas.RatingUpdate, db: Session = Depends(get_db)):
    db_rating = crud.update_rating(db, rating_id=rating_id, rating_update=rating)
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return db_rating

@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT) # Changed status_code for successful deletion
def delete_rating_general(rating_id: int, db: Session = Depends(get_db)):
    db_rating = crud.delete_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT) # FastAPI convention for 204

@router.get("/user/{user_id}", response_model=List[schemas.RatingResponse])
def get_ratings_by_user(user_id: int, db: Session = Depends(get_db)):
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found for this user")
    return ratings

@router.get("/game/{game_id}", response_model=List[schemas.RatingResponse])
def get_ratings_by_game(game_id: int, db: Session = Depends(get_db)):
    ratings = crud.get_ratings_by_game(db, game_id=game_id)
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found for this game")
    return ratings

@router.options("/")
def options_ratings():
    return {"message": "OPTIONS successful"}


# --- User-Specific Rating Endpoints (MOVED from users.py) ---
# These paths are relative to the /ratings prefix that will be added in main.py
# So, /me will become /ratings/me
# And / will become /ratings/ for create/post

@router.post("/", response_model=schemas.RatingResponse) # This will be POST /ratings/
def create_my_rating(
    rating_data: schemas.RatingCreateMe, # Use RatingCreateMe for user's own rating, if different from general
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # This logic comes directly from your users.py
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


@router.get("/me", response_model=List[schemas.RatingResponse]) # This will be GET /ratings/me
def read_my_ratings( # Renamed for clarity
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


@router.get("/me/{rating_id}", response_model=schemas.RatingResponse) # This will be GET /ratings/me/{rating_id}
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


@router.put("/me/{rating_id}", response_model=schemas.RatingResponse) # This will be PUT /ratings/me/{rating_id}
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


@router.delete("/me/{rating_id}", status_code=status.HTTP_204_NO_CONTENT) # This will be DELETE /ratings/me/{rating_id}
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
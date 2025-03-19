# app/routers/ratings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas
from app.database.session import get_db

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/", response_model=schemas.Ratings)
def create_rating(rating: schemas.RatingsCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=rating.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_game = crud.get_game(db, game_id=rating.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_rating(db=db, rating=rating)

@router.get("/{rating_id}", response_model=schemas.Ratings)
def read_rating(rating_id: int, db: Session = Depends(get_db)):
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return db_rating

@router.get("/", response_model=list[schemas.Ratings])
def read_ratings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ratings = crud.get_ratings(db, skip=skip, limit=limit)
    return ratings

@router.put("/{rating_id}", response_model=schemas.Ratings)
def update_rating(rating_id: int, rating: schemas.RatingsUpdate, db: Session = Depends(get_db)):
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

    if rating.user_id is not None:
        db_user = crud.get_user(db, user_id=rating.user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if rating.game_id is not None:
        db_game = crud.get_game(db, game_id=rating.game_id)
        if not db_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_rating(db=db, rating_id=rating_id, rating_update=rating)

@router.delete("/{rating_id}", response_model=schemas.Ratings)
def delete_rating(rating_id: int, db: Session = Depends(get_db)):
    db_rating = crud.delete_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return db_rating


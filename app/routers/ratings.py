# app/routers/ratings.py
# This file's contents are now managed and included via app/routers/users.py
# All user-specific rating endpoints are now under /users/me/ratings/
# Uncomment or define new routes here only if needed for non-user-specific
# rating management (e.g., admin listing all ratings)

# from typing import List
#
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
#
# from app.database import crud, models, schemas
# from app.database.session import get_db
#
# router = APIRouter(prefix="/ratings", tags=["ratings"])
#
#
# @router.post("/", response_model=schemas.Rating, status_code=status.HTTP_201_CREATED)
# def create_rating(rating: schemas.RatingCreate, db: Session = Depends(get_db)):
#     return crud.create_rating(db=db, rating=rating)
#
#
# @router.get("/{rating_id}", response_model=schemas.Rating)
# def read_rating(rating_id: int, db: Session = Depends(get_db)):
#     db_rating = crud.get_rating(db, rating_id=rating_id)
#     if db_rating is None:
#         raise HTTPException(status_code=404, detail="Rating not found")
#     return db_rating
#
#
# @router.get("/", response_model=List[schemas.Rating])
# def read_ratings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     ratings = crud.get_ratings(db, skip=skip, limit=limit)
#     return ratings
#
#
# @router.put("/{rating_id}", response_model=schemas.Rating)
# def update_rating(rating_id: int, rating: schemas.RatingUpdate, db: Session = Depends(get_db)):
#     db_rating = crud.update_rating(db, rating_id=rating_id, rating_update=rating)
#     if db_rating is None:
#         raise HTTPException(status_code=404, detail="Rating not found")
#     return db_rating
#
#
# @router.delete("/{rating_id}", status_code=status.HTTP_200_OK, response_model=schemas.Rating)
# def delete_rating(rating_id: int, db: Session = Depends(get_db)):
#     db_rating = crud.delete_rating(db, rating_id=rating_id)
#     if db_rating is None:
#         raise HTTPException(status_code=404, detail="Rating not found")
#     return db_rating
#
#
# @router.get("/user/{user_id}", response_model=List[schemas.Rating])
# def get_ratings_by_user(user_id: int, db: Session = Depends(get_db)):
#     ratings = crud.get_ratings_by_user(db, user_id=user_id)
#     if not ratings:
#         raise HTTPException(status_code=404, detail="No ratings found for this user")
#     return ratings
#
# @router.get("/game/{game_id}", response_model=List[schemas.Rating])
# def get_ratings_by_game(game_id: int, db: Session = Depends(get_db)):
#     ratings = crud.get_ratings_by_game(db, game_id=game_id)
#     if not ratings:
#         raise HTTPException(status_code=404, detail="No ratings found for this game")
#     return ratings
#
# @router.options("/")
# def options_ratings():
#     return {"message": "OPTIONS successful"}
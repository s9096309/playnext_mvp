from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/", response_model=schemas.Rating)
def create_rating(rating: schemas.RatingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a new rating.
    """
    # Ensure that the user_id in the request matches the current user's ID
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
def read_rating(rating_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve a rating by ID.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return db_rating

@router.get("/", response_model=list[schemas.Rating])
def read_ratings(skip: int = 0, limit: int = 100, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve a list of ratings.
    """
    ratings = crud.get_ratings(db, skip=skip, limit=limit)
    return ratings

@router.put("/{rating_id}", response_model=schemas.Rating)
def update_rating(rating_id: int, rating: schemas.RatingUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Update a rating.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this rating")

    if rating.game_id is not None:
        db_game = crud.get_game(db, game_id=rating.game_id)
        if not db_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_rating(db=db, rating_id=rating_id, rating_update=rating)

@router.delete("/{rating_id}", response_model=schemas.Rating)
def delete_rating(rating_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete a rating.
    """
    db_rating = crud.get_rating(db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")

    if db_rating.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this rating")

    return crud.delete_rating(db, rating_id=rating_id)

@router.get("/user/{user_id}", response_model=list[schemas.Rating])
def read_user_ratings(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get all ratings for a specific user.
    """
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ratings not found for this user")
    return ratings

@router.get("/game/{game_id}", response_model=list[schemas.Rating])
def read_game_ratings(game_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get all ratings for a specific game.
    """
    return crud.get_game_ratings(db, game_id=game_id)

@router.options("/")
async def ratings_options(request: Request):
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "file://",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })

@router.post("/me/")
def create_user_rating(rating: schemas.RatingCreateMe, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Create a rating for the currently authenticated user.
    """
    rating_data = schemas.RatingCreate(
        user_id=current_user.user_id,
        game_id=rating.game_id,
        rating=rating.rating,
        comment=rating.comment,
        rating_date=rating.rating_date
    )

    db_game = crud.get_game(db, game_id=rating.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_rating(db=db, rating=rating_data)
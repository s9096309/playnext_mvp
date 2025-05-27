from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import models, schemas
from app.database.session import get_db
# FROM app.database import crud  <-- REMOVE OR COMMENT THIS OUT
from app.database import user_crud # <-- ADD THIS LINE
from app.utils.auth import get_current_user # Assuming this handles authentication


router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(db=db, user=schemas.UserCreateDB(**user.dict()))

@router.get("/me", response_model=schemas.User)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.get("/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to read all users."
        )
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, current_user: models.User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """
    Update a user's profile.
    """
    if user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    db_user = crud.update_user(db, user_id=user_id, user_update=user)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete a user.
    """
    if user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/me", response_model=schemas.User)
def update_current_user(user_update: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.update_user(db=db, user_id=current_user.user_id, user=user_update)

@router.delete("/me", response_model=schemas.User)
def delete_current_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    crud.delete_user(db, user_id=current_user.user_id)
    return current_user

@router.get("/me/backlog", response_model=list[schemas.BacklogItem])
def read_users_me_backlog(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the backlog of the currently authenticated user.
    """
    backlog_items = user_crud.get_user_backlog(db, user_id=current_user.user_id)
    return backlog_items

@router.get("/me/ratings", response_model=list[schemas.Rating])
def read_users_me_ratings(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the ratings of the currently authenticated user.
    """
    ratings = user_crud.get_ratings_by_user(db, user_id=current_user.user_id)
    return ratings

@router.get("/me/recommendations", response_model=schemas.RecommendationResponse)
async def read_users_me_recommendations(current_user: models.User = Depends(get_current_user),
                                        db: Session = Depends(get_db)):
    """
    Get the recommendations for the currently authenticated user.
    """
    user_request = schemas.UserRequest(user_id=current_user.user_id)
    return await recommendations.get_user_recommendations(user_request=user_request, db=db)
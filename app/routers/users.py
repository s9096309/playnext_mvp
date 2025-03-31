from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the profile of the currently authenticated user.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the profile of a specific user.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.get("/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get a list of users.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@router.get("/me/backlog", response_model=list[schemas.BacklogItem])
def read_users_me_backlog(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the backlog of the currently authenticated user.
    """
    backlog_items = crud.get_user_backlog(db, user_id=current_user.user_id)
    return backlog_items

@router.get("/me/ratings", response_model=list[schemas.Rating])
def read_users_me_ratings(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the ratings of the currently authenticated user.
    """
    ratings = crud.get_user_ratings(db, user_id=current_user.user_id)
    return ratings

@router.get("/me/recommendations", response_model=list[schemas.Recommendation])
def read_users_me_recommendations(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the recommendations for the currently authenticated user.
    """
    recommendations = crud.get_user_recommendations(db, user_id=current_user.user_id)
    return recommendations
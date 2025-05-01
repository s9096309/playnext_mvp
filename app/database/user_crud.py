# app/database/user_crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from typing import List
from datetime import datetime

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreateDB, is_admin: bool = False):
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        user_age=user.user_age,
        is_admin=is_admin,
        registration_date=datetime.utcnow()  # Explicitly set the registration date
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_backlog(db: Session, user_id: int) -> List[models.BacklogItem]:
    return db.query(models.BacklogItem).filter(models.BacklogItem.user_id == user_id).all()

def get_ratings_by_user(db: Session, user_id: int) -> List[models.Rating]:
    return db.query(models.Rating).filter(models.Rating.user_id == user_id).all()
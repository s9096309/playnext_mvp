from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
import enum

class BacklogStatus(str, enum.Enum):
    playing = "playing"
    completed = "completed"
    dropped = "dropped"

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    password_hash: str
    registration_date: datetime
    user_age: Optional[int] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    registration_date: Optional[datetime] = None
    user_age: Optional[int] = None

class User(UserBase):
    user_id: int

    class Config:
        from_attributes = True

# Game Schemas
class GameBase(BaseModel):
    game_name: str
    genre: str
    release_date: date
    platform: str
    igdb_id: int
    image_url: Optional[str] = None
    age_rating: Optional[str] = None

class GameCreate(GameBase):
    pass

class GameUpdate(BaseModel):
    game_name: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[date] = None
    platform: Optional[str] = None
    igdb_id: Optional[int] = None
    image_url: Optional[str] = None
    age_rating: Optional[str] = None #age rating is now string

class Game(GameBase):
    game_id: int

    class Config:
        from_attributes = True

# BacklogItem Schemas
class BacklogItemBase(BaseModel):
    user_id: int
    game_id: int
    status: BacklogStatus
    rating: Optional[float] = None
    play_status: Optional[str] = None

class BacklogItemCreate(BacklogItemBase):
    pass

class BacklogItemUpdate(BaseModel):
    user_id: Optional[int] = None
    game_id: Optional[int] = None
    status: Optional[BacklogStatus] = None
    rating: Optional[float] = None
    play_status: Optional[str] = None

class BacklogItem(BacklogItemBase):
    backlog_id: int

    class Config:
        from_attributes = True

# Recommendation Schemas
class RecommendationBase(BaseModel):
    user_id: int
    game_id: int
    timestamp: datetime
    recommendation_reason: str
    documentation_rating: Optional[float] = None

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationUpdate(BaseModel):
    user_id: Optional[int] = None
    game_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    recommendation_reason: Optional[str] = None
    documentation_rating: Optional[float] = None

class Recommendation(RecommendationBase):
    recommendation_id: int

    class Config:
        from_attributes = True

# Rating Schemas
class RatingBase(BaseModel):
    user_id: int
    game_id: int
    rating: float
    comment: Optional[str] = None
    rating_date: datetime

class RatingCreate(RatingBase):
    pass

class RatingUpdate(BaseModel):
    user_id: Optional[int] = None
    game_id: Optional[int] = None
    rating: Optional[float] = None
    comment: Optional[str] = None
    rating_date: Optional[datetime] = None

class Rating(RatingBase):
    rating_id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class RatingCreateMe(BaseModel):
    game_id: int
    rating: float
    comment: str
    rating_date: datetime
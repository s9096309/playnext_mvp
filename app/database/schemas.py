# app/database/schemas.py

from datetime import datetime, date
import enum
from typing import Optional, List

from pydantic import BaseModel


class BacklogStatus(str, enum.Enum):
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"


class BacklogItemCreate(BaseModel):
    user_id: int
    game_id: int
    status: BacklogStatus
    rating: Optional[float] = None


class BacklogItemUpdate(BaseModel):
    user_id: Optional[int] = None
    game_id: Optional[int] = None
    status: Optional[BacklogStatus] = None
    rating: Optional[float] = None


class BacklogItem(BaseModel):
    backlog_id: int
    user_id: int
    game_id: int
    status: BacklogStatus
    rating: Optional[float] = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: str
    user_age: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserCreateDB(UserBase):
    password_hash: str
    registration_date: datetime
    is_admin: bool


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    user_age: Optional[int] = None
    is_admin: Optional[bool] = None


class User(UserBase):
    user_id: int
    password_hash: str
    registration_date: datetime
    is_admin: bool

    class Config:
        from_attributes = True


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
    age_rating: Optional[str] = None


class Game(GameBase):
    game_id: int

    class Config:
        from_attributes = True


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


class StructuredRecommendation(BaseModel):
    game_name: str
    genre: str
    igdb_link: Optional[str] = None
    reasoning: Optional[str] = None


class RecommendationResponse(BaseModel):
    structured_recommendations: List[StructuredRecommendation]
    gemini_response: str


class UserRequest(BaseModel):
    user_id: int
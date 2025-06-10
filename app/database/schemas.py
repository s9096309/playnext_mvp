import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BacklogStatus(str, enum.Enum):
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"
    PLANNING = "planning"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    igdb_id: Optional[int] = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    user_age: Optional[int] = None


class UserCreateDB(UserBase):
    password_hash: str
    registration_date: datetime.datetime
    user_age: Optional[int] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    user_age: Optional[int] = None
    igdb_id: Optional[int] = None
    is_admin: Optional[bool] = None

    class Config:
        from_attributes = True


class User(UserBase):
    user_id: int
    registration_date: datetime.datetime
    user_age: Optional[int] = None

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    game_name: str
    genre: Optional[str] = None
    release_date: Optional[datetime.date] = None
    platform: Optional[str] = None
    igdb_id: int
    image_url: Optional[str] = None
    age_rating: Optional[str] = None
    igdb_link: Optional[str] = None

    class Config:
        from_attributes = True


class GameCreate(GameBase):
    pass


class GameUpdate(BaseModel):
    game_name: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[datetime.date] = None
    platform: Optional[str] = None
    igdb_link: Optional[str] = None
    image_url: Optional[str] = None
    age_rating: Optional[str] = None

    class Config:
        from_attributes = True


class Game(GameBase):
    game_id: int

    class Config:
        from_attributes = True


class BacklogItemBase(BaseModel):
    user_id: int
    game_id: int
    status: BacklogStatus

    class Config:
        from_attributes = True


class BacklogItemCreate(BacklogItemBase):
    pass


class BacklogItemUpdate(BaseModel):
    status: Optional[BacklogStatus] = None
    game_id: Optional[int] = None

    class Config:
        from_attributes = True


class BacklogItem(BacklogItemBase):
    backlog_id: int
    added_date: datetime.datetime

    class Config:
        from_attributes = True


class RecommendationBase(BaseModel):
    user_id: int
    game_id: int
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    recommendation_reason: str
    documentation_rating: float
    raw_gemini_output: Optional[str] = None
    structured_json_output: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationUpdate(BaseModel):
    timestamp: Optional[datetime.datetime] = None
    recommendation_reason: Optional[str] = None
    documentation_rating: Optional[float] = None
    raw_gemini_output: Optional[str] = None
    structured_json_output: Optional[str] = None

    class Config:
        from_attributes = True


class Recommendation(RecommendationBase):
    recommendation_id: int

    class Config:
        from_attributes = True


class RatingBase(BaseModel):
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: datetime.datetime

    class Config:
        from_attributes = True


class RatingCreate(RatingBase):
    pass


class RatingUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1.0, le=10.0)
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class Rating(RatingBase):
    rating_id: int

    class Config:
        from_attributes = True


class RatingCreateMe(BaseModel):
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class RatingResponse(BaseModel):
    rating_id: int
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    game: Optional["Game"] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class StructuredRecommendation(BaseModel):
    game_name: str = Field(..., alias="name")
    genre: str
    igdb_link: Optional[str] = None
    reasoning: str

    class Config:
        populate_by_name = True


class RecommendationResponse(BaseModel):
    structured_recommendations: List[StructuredRecommendation]
    gemini_response: Optional[str] = None


class UserRequest(BaseModel):
    user_id: int
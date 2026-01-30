"""
Pydantic schemas for the PlayNext application.

These schemas define the data structures for request and response bodies,
and for interacting with SQLAlchemy models.
"""

import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class BacklogStatus(str, enum.Enum):
    """Enumeration for the status of a game in a user's backlog."""
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"
    PLANNING = "planning"


class UserBase(BaseModel):
    """Base Pydantic schema for user data."""
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Pydantic schema for creating a new user."""
    password: str = Field(..., min_length=8)
    user_age: Optional[int] = None


class UserCreateDB(UserBase):
    """Pydantic schema for creating a user record in the database."""
    hashed_password: str
    registration_date: datetime.datetime
    user_age: Optional[int] = None
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Pydantic schema for updating an existing user."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    user_age: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    """Pydantic schema for a user retrieved from the database."""
    user_id: int
    registration_date: datetime.datetime
    user_age: Optional[int] = None
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class GameBase(BaseModel):
    """Base Pydantic schema for game data."""
    game_name: str
    genre: Optional[str] = None
    release_date: Optional[datetime.date] = None
    platform: Optional[str] = None
    igdb_id: int
    image_url: Optional[str] = None
    age_rating: Optional[str] = None
    igdb_link: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GameCreate(GameBase):
    """Pydantic schema for creating a new game."""


class GameUpdate(BaseModel):
    """Pydantic schema for updating an existing game."""
    game_name: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[datetime.date] = None
    platform: Optional[str] = None
    igdb_link: Optional[str] = None
    image_url: Optional[str] = None
    age_rating: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Game(GameBase):
    """Pydantic schema for a game retrieved from the database."""
    game_id: int

    model_config = ConfigDict(from_attributes=True)


class BacklogItemBase(BaseModel):
    """Base Pydantic schema for backlog item data."""
    user_id: int
    game_id: int
    status: BacklogStatus

    model_config = ConfigDict(from_attributes=True)


class BacklogItemCreate(BacklogItemBase):
    """Pydantic schema for creating a new backlog item."""


class BacklogItemUpdate(BaseModel):
    """Pydantic schema for updating an existing backlog item."""
    status: Optional[BacklogStatus] = None
    game_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class BacklogItem(BacklogItemBase):
    """Pydantic schema for a backlog item retrieved from the database."""
    backlog_id: int
    added_date: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationBase(BaseModel):
    """Base Pydantic schema for recommendation data."""
    user_id: int
    game_id: int
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    recommendation_reason: str
    documentation_rating: float
    raw_gemini_output: Optional[str] = None
    structured_json_output: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationCreate(RecommendationBase):
    """Pydantic schema for creating a new recommendation."""


class RecommendationUpdate(BaseModel):
    """Pydantic schema for updating an existing recommendation."""
    timestamp: Optional[datetime.datetime] = None
    recommendation_reason: Optional[str] = None
    documentation_rating: Optional[float] = None
    raw_gemini_output: Optional[str] = None
    structured_json_output: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Recommendation(RecommendationBase):
    """Pydantic schema for a recommendation retrieved from the database."""
    recommendation_id: int

    model_config = ConfigDict(from_attributes=True)


class RatingBase(BaseModel):
    """Base Pydantic schema for rating data."""
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class RatingCreate(RatingBase):
    """Pydantic schema for creating a new rating."""


class RatingUpdate(BaseModel):
    """Pydantic schema for updating an existing rating."""
    rating: Optional[float] = Field(None, ge=1.0, le=10.0)
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Rating(RatingBase):
    """Pydantic schema for a rating retrieved from the database."""
    rating_id: int
    updated_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RatingCreateMe(BaseModel):
    """Pydantic schema for a user to create their own rating."""
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RatingResponse(BaseModel):
    """Pydantic schema for a detailed rating response, including related game data."""
    rating_id: int
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0)
    comment: Optional[str] = None
    rating_date: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    game: Optional["Game"] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Pydantic schema for authentication token."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Pydantic schema for data contained within an authentication token."""
    username: Optional[str] = None


class StructuredRecommendation(BaseModel):
    """Pydantic schema for a single structured game recommendation."""
    game_name: str = Field(..., alias="name")
    genre: str
    igdb_link: Optional[str] = None
    reasoning: str

    model_config = ConfigDict(populate_by_name=True)


class RecommendationResponse(BaseModel):
    """Pydantic schema for a collection of structured recommendations and raw Gemini output."""
    structured_recommendations: List[StructuredRecommendation]
    gemini_response: Optional[str] = None


class UserRequest(BaseModel):
    """Pydantic schema for a user ID in a request body."""
    user_id: int

class UserInRating(BaseModel):
    """Pydantic schema for user information nested within a rating."""
    user_id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class GameInRating(BaseModel):
    """Pydantic schema for game information nested within a rating."""
    game_id: int
    game_name: str
    image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RatingWithUserAndGame(BaseModel):
    """Pydantic schema for a rating including nested user and game details."""
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    rating_id: int
    user_id: int
    game_id: int
    rating: float
    comment: Optional[str] = None
    rating_date: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    user: UserInRating
    game: GameInRating
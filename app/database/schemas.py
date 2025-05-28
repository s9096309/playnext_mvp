# app/database/schemas.py

"""
Pydantic schemas for data validation and serialization in the PlayNext API.

These schemas define the structure of data for requests and responses,
ensuring type safety and data integrity.
"""

import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BacklogStatus(str, enum.Enum):
    """Enum for the possible statuses of a game in a user's backlog."""
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"
    PLANNING = "planning"


class UserBase(BaseModel):
    """Base Pydantic schema for user data."""
    username: str
    email: EmailStr
    igdb_id: Optional[int] = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Pydantic schema for creating a new user (API input)."""
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")
    user_age: Optional[int] = None # <-- KEEP THIS ADDITION (Fixes 'UserCreate' object has no attribute 'user_age')

class UserCreateDB(UserBase):
    """Pydantic schema for user data as stored in the database (internal creation)."""
    password_hash: str
    registration_date: datetime.datetime
    user_age: Optional[int] = None


    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Pydantic schema for updating an existing user."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, description="New password (optional, minimum 8 characters)")
    user_age: Optional[int] = None
    igdb_id: Optional[int] = None
    is_admin: Optional[bool] = None

    class Config:
        from_attributes = True


class User(UserBase):
    """Pydantic schema for a complete user record, typically returned by the API."""
    user_id: int
    registration_date: datetime.datetime
    user_age: Optional[int] = None

    class Config:
        from_attributes = True


class GameBase(BaseModel):
    """Base Pydantic schema for game data."""
    game_name: str
    genre: str
    release_date: datetime.date
    platform: str
    igdb_id: int
    image_url: Optional[str] = None
    age_rating: Optional[int] = Field(None, ge=0, description="Game age rating (e.g., PEGI, ESRB equivalent)")

    class Config:
        from_attributes = True


class GameCreate(GameBase):
    """Pydantic schema for creating a new game."""
    pass


class GameUpdate(BaseModel):
    """Pydantic schema for updating an existing game."""
    game_name: Optional[str] = None
    genre: Optional[str] = None
    release_date: Optional[datetime.date] = None
    platform: Optional[str] = None
    image_url: Optional[str] = None
    age_rating: Optional[int] = Field(None, ge=0, description="Updated age rating")

    class Config:
        from_attributes = True


class Game(GameBase):
    """Pydantic schema for a complete game record, including relationships."""
    game_id: int

    class Config:
        from_attributes = True


class BacklogItemBase(BaseModel):
    """Base Pydantic schema for backlog item data."""
    user_id: int
    game_id: int
    status: BacklogStatus

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BacklogItemCreate(BacklogItemBase):
    """Pydantic schema for creating a new backlog item."""
    pass


class BacklogItemUpdate(BaseModel):
    """Pydantic schema for updating an existing backlog item."""
    status: Optional[BacklogStatus] = None
    game_id: Optional[int] = None # Keep this if you want to allow changing the associated game

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BacklogItem(BacklogItemBase):
    """Pydantic schema for a complete backlog item record."""
    backlog_id: int
    added_date: datetime.datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RecommendationBase(BaseModel):
    """Base Pydantic schema for recommendation data."""
    user_id: int
    game_id: int
    timestamp: datetime.datetime
    recommendation_reason: str
    documentation_rating: float = Field(..., ge=0.0, le=5.0, description="Rating for documentation quality (0.0-5.0)")

    class Config:
        from_attributes = True


class RecommendationCreate(RecommendationBase):
    """Pydantic schema for creating a new recommendation."""
    pass


class RecommendationUpdate(BaseModel):
    """Pydantic schema for updating an existing recommendation."""
    recommendation_reason: Optional[str] = None
    documentation_rating: Optional[float] = Field(None, ge=0.0, le=5.0)

    class Config:
        from_attributes = True


class Recommendation(RecommendationBase):
    """Pydantic schema for a complete recommendation record."""
    recommendation_id: int

    class Config:
        from_attributes = True


class RatingBase(BaseModel):
    """Base Pydantic schema for rating data."""
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0, description="User's rating for the game (1.0-10.0)")
    comment: Optional[str] = None
    rating_date: datetime.datetime

    class Config:
        from_attributes = True


class RatingCreate(RatingBase):
    """Pydantic schema for creating a new rating."""
    pass


class RatingUpdate(BaseModel):
    """Pydantic schema for updating an existing rating."""
    rating: Optional[float] = Field(None, ge=1.0, le=10.0)
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class Rating(RatingBase):
    """Pydantic schema for a complete rating record."""
    rating_id: int

    class Config:
        from_attributes = True


# --- NEWLY ADDED SCHEMAS / FIXES BELOW THIS LINE ---

class Token(BaseModel):
    """Pydantic schema for OAuth2 access token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Pydantic schema for data stored inside a JWT token."""
    username: Optional[str] = None

class StructuredRecommendation(BaseModel):
    """Pydantic schema for a single structured game recommendation."""
    game_name: str
    genre: str
    igdb_link: str # Link to the game on IGDB for more details
    reasoning: str # Why this game is recommended

class RecommendationResponse(BaseModel):
    """Pydantic schema for the full response from the recommendation endpoint."""
    structured_recommendations: List[StructuredRecommendation]
    gemini_response: Optional[str] = None # Optional, for raw AI output or debugging

class UserRequest(BaseModel):
    """Pydantic schema for a user ID request, typically for recommendation generation."""
    user_id: int

class RatingCreateMe(BaseModel):
    """
    Pydantic schema for creating a new rating *by the current user*.
    Excludes user_id as it's inferred from authentication.
    """
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0, description="User's rating for the game (1.0-10.0)")
    comment: Optional[str] = None
    rating_date: Optional[datetime.datetime] = None # Optional, will default to now if not provided

    class Config:
        from_attributes = True
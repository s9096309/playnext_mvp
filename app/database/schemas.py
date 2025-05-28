# app/database/schemas.py

"""
Pydantic schemas for data validation and serialization in the PlayNext API.

These schemas define the structure of data for requests and responses,
ensuring type safety and data integrity.
"""

import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field # Added EmailStr and Field for better validation


class BacklogStatus(str, enum.Enum):
    """Enum for the possible statuses of a game in a user's backlog."""
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"
    # Added for completeness, if your application supports these statuses
    ON_HOLD = "on_hold"
    PLANNING = "planning"


class UserBase(BaseModel):
    """Base Pydantic schema for user data."""
    username: str
    email: EmailStr # Using EmailStr for better email validation
    igdb_id: Optional[int] = None
    is_admin: bool = False

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserCreate(UserBase):
    """Pydantic schema for creating a new user (API input)."""
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


# RENAMED UserInDBBase to UserCreateDB to match user_crud.py's expectation
# This schema is used internally for creating a user record in the database,
# including the hashed password and registration date.
class UserCreateDB(UserBase):
    """Pydantic schema for user data as stored in the database (internal creation)."""
    password_hash: str # This will store the hashed password
    registration_date: datetime.datetime
    user_age: Optional[int] = None # Assuming user_age is passed or handled here


    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserUpdate(BaseModel):
    """Pydantic schema for updating an existing user."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None # Using EmailStr
    password: Optional[str] = Field(None, min_length=8, description="New password (optional, minimum 8 characters)")
    user_age: Optional[int] = None
    igdb_id: Optional[int] = None
    is_admin: Optional[bool] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class User(UserBase):
    """Pydantic schema for a complete user record, including relationships.
    This is what is typically returned by the API.
    """
    user_id: int
    registration_date: datetime.datetime
    user_age: Optional[int] = None # Inherited from UserBase or explicitly defined here


    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class GameBase(BaseModel):
    """Base Pydantic schema for game data."""
    game_name: str
    genre: str
    release_date: datetime.date
    platform: str
    igdb_id: int
    image_url: Optional[str] = None
    # Changed to int for age ratings (e.g., PEGI 18, ESRB M, which are numeric values)
    age_rating: Optional[int] = Field(None, ge=0, description="Game age rating (e.g., PEGI, ESRB equivalent)")

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
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
    age_rating: Optional[int] = Field(None, ge=0, description="Updated age rating") # Changed to int

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class Game(GameBase):
    """Pydantic schema for a complete game record, including relationships."""
    game_id: int

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BacklogItemBase(BaseModel):
    """Base Pydantic schema for backlog item data."""
    user_id: int
    game_id: int
    status: BacklogStatus
    rating: Optional[float] = Field(None, ge=1.0, le=10.0, description="User's rating for the game (1.0-10.0)")
    hours_played: Optional[float] = Field(None, ge=0.0, description="Hours played on the game")
    start_date: Optional[datetime.date] = None
    completion_date: Optional[datetime.date] = None
    notes: Optional[str] = None


    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BacklogItemCreate(BacklogItemBase):
    """Pydantic schema for creating a new backlog item."""
    pass


class BacklogItemUpdate(BaseModel):
    """Pydantic schema for updating an existing backlog item."""
    status: Optional[BacklogStatus] = None
    rating: Optional[float] = Field(None, ge=1.0, le=10.0)
    # Added for completeness
    hours_played: Optional[float] = Field(None, ge=0.0)
    start_date: Optional[datetime.date] = None
    completion_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    game_id: Optional[int] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BacklogItem(BacklogItemBase):
    """Pydantic schema for a complete backlog item record."""
    backlog_id: int
    added_date: datetime.datetime
    # pylint: disable=too-few-public-methods
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

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RecommendationCreate(RecommendationBase):
    """Pydantic schema for creating a new recommendation."""
    pass


class RecommendationUpdate(BaseModel):
    """Pydantic schema for updating an existing recommendation."""
    recommendation_reason: Optional[str] = None
    documentation_rating: Optional[float] = Field(None, ge=0.0, le=5.0)

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class Recommendation(RecommendationBase):
    """Pydantic schema for a complete recommendation record."""
    recommendation_id: int

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RatingBase(BaseModel):
    """Base Pydantic schema for rating data."""
    user_id: int
    game_id: int
    rating: float = Field(..., ge=1.0, le=10.0, description="User's rating for the game (1.0-10.0)")
    comment: Optional[str] = None
    rating_date: datetime.datetime

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RatingCreate(RatingBase):
    """Pydantic schema for creating a new rating."""
    pass


class RatingUpdate(BaseModel):
    """Pydantic schema for updating an existing rating."""
    rating: Optional[float] = Field(None, ge=1.0, le=10.0)
    comment: Optional[str] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class Rating(RatingBase):
    """Pydantic schema for a complete rating record."""
    rating_id: int

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True
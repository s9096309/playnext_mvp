# app/database/schemas.py

"""
Pydantic schemas for data validation and serialization in the PlayNext API.

These schemas define the structure of data for requests and responses,
ensuring type safety and data integrity.
"""

import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel


class BacklogStatus(str, enum.Enum):
    """Enum for the possible statuses of a game in a user's backlog."""
    PLAYING = "playing"
    COMPLETED = "completed"
    DROPPED = "dropped"


class UserBase(BaseModel):
    """Base Pydantic schema for user data."""
    username: str
    email: str
    igdb_id: Optional[int] = None
    is_admin: bool = False

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserCreate(UserBase):
    """Pydantic schema for creating a new user."""
    password: str


class UserUpdate(BaseModel):
    """Pydantic schema for updating an existing user."""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    user_age: Optional[int] = None
    igdb_id: Optional[int] = None
    is_admin: Optional[bool] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserInDBBase(UserBase):
    """Pydantic schema for user data as stored in the database."""
    user_id: int
    registration_date: datetime.datetime
    user_age: Optional[int] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class User(UserInDBBase):
    """Pydantic schema for a complete user record, including relationships."""
    pass


class GameBase(BaseModel):
    """Base Pydantic schema for game data."""
    game_name: str
    genre: str
    release_date: datetime.date
    platform: str
    igdb_id: int
    image_url: Optional[str] = None
    age_rating: Optional[str] = None

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
    age_rating: Optional[str] = None

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
    rating: Optional[float] = None

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
    rating: Optional[float] = None

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
    documentation_rating: float

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
    documentation_rating: Optional[float] = None

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
    rating: float
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
    rating: Optional[float] = None
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
"""
SQLAlchemy ORM models for the PlayNext application.

This module defines the database schema and relationships between tables
for users, games, recommendations, ratings, and user backlogs.
"""

from datetime import datetime, UTC
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Float, Text, Boolean
)
from sqlalchemy.orm import relationship

from .session import Base


class User(Base):
    """
    SQLAlchemy model for the 'users' table.

    Represents a user in the system with authentication details,
    profile information, and relationships to their recommendations,
    ratings, and backlog entries.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    registration_date = Column(DateTime, default=datetime.now(UTC), nullable=False)
    user_age = Column(Integer, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    recommendations = relationship("Recommendation", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    backlog_entries = relationship("Backlog", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Game(Base):
    """
    SQLAlchemy model for the 'games' table.

    Stores information about individual games, including their IGDB details
    and relationships to user-generated data like recommendations, ratings,
    and backlog entries.
    """
    __tablename__ = "games"
    game_id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String, unique=True, index=True, nullable=False)
    genre = Column(String)
    release_date = Column(String)
    platform = Column(String)
    igdb_id = Column(Integer, unique=True, index=True)
    image_url = Column(String)
    age_rating = Column(String)
    igdb_link = Column(String)

    recommendations = relationship(
        "Recommendation",
        back_populates="game",
        cascade="all, delete-orphan"
    )
    ratings = relationship(
        "Rating",
        back_populates="game",
        cascade="all, delete-orphan"
    )
    backlog_entries = relationship(
        "Backlog",
        back_populates="game",
        cascade="all, delete-orphan"
    )


class Recommendation(Base):
    """
    SQLAlchemy model for the 'recommendations' table.

    Represents a game recommendation generated for a user, including
    the reason, documentation rating, and raw/structured AI output.
    """
    __tablename__ = "recommendations"
    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    recommendation_reason = Column(Text)
    documentation_rating = Column(Float)
    raw_gemini_output = Column(Text)
    structured_json_output = Column(Text)

    user = relationship("User", back_populates="recommendations")
    game = relationship("Game", back_populates="recommendations")


class Rating(Base):
    """
    SQLAlchemy model for the 'ratings' table.

    Stores user-provided ratings and optional comments for games.
    """
    __tablename__ = "ratings"
    rating_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String)
    rating_date = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="ratings")
    game = relationship("Game", back_populates="ratings")


class Backlog(Base):
    """
    SQLAlchemy model for the 'backlog' table.

    Represents a game in a user's personal backlog, indicating its
    status (e.g., 'Playing', 'Completed', 'Plan to Play').
    """
    __tablename__ = "backlog"
    backlog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    added_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    rating = Column(Integer)

    user = relationship("User", back_populates="backlog_entries")
    game = relationship("Game", back_populates="backlog_entries")
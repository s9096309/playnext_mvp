# app/database/models.py

"""
SQLAlchemy models for the PlayNext database.

This module defines the database schema for users, games, ratings,
backlog items, and recommendations using SQLAlchemy's declarative base.
"""
from app.database.schemas import BacklogStatus
import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    """SQLAlchemy model for the 'users' table."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    registration_date = Column(DateTime)
    user_age = Column(Integer)
    igdb_id = Column(Integer, nullable=True)
    is_admin = Column(Boolean, default=False)

    backlog_items = relationship("BacklogItem", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
    ratings = relationship("Rating", back_populates="user")


class Game(Base):
    """SQLAlchemy model for the 'games' table."""
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String, index=True)
    genre = Column(String)
    release_date = Column(Date)
    platform = Column(String)
    igdb_id = Column(Integer, unique=True, index=True)
    image_url = Column(String)
    age_rating = Column(String)

    backlog_items = relationship("BacklogItem", back_populates="game")
    ratings = relationship("Rating", back_populates="game")



class BacklogItem(Base):
    """SQLAlchemy model for the 'backlog_items' table."""
    __tablename__ = "backlog_items"

    backlog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    status = Column(Enum(BacklogStatus, values_callable=lambda obj: [e.value for e in obj], native_enum=False))
    rating = Column(Float, nullable=True)
    added_date = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="backlog_items")
    game = relationship("Game", back_populates="backlog_items")


class Recommendation(Base):
    """SQLAlchemy model for the 'recommendations' table (updated for caching Gemini response)."""
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True) # Added index for faster lookups
    generation_timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Fields to store the raw and structured JSON output from Gemini
    raw_gemini_output = Column(String)
    structured_json_output = Column(String)

    user = relationship("User", back_populates="recommendations")


class Rating(Base):
    """SQLAlchemy model for the 'ratings' table."""
    __tablename__ = "ratings"

    rating_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    rating = Column(Float)
    comment = Column(String)
    rating_date = Column(DateTime)
    updated_at = Column(DateTime)

    user = relationship("User", back_populates="ratings")
    game = relationship("Game", back_populates="ratings")
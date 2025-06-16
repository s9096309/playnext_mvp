# app/database/models.py

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, Boolean, BigInteger
from sqlalchemy.orm import relationship

from .session import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    registration_date = Column(DateTime, default=datetime.now(UTC), nullable=False)
    user_age = Column(Integer, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    igdb_id = Column(Integer, unique=True, index=True, nullable=True)

    recommendations = relationship("Recommendation", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    backlog_entries = relationship("Backlog", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"




class Game(Base):
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
    __tablename__ = "backlog"
    backlog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    added_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    rating = Column(Integer)

    user = relationship("User", back_populates="backlog_entries")
    game = relationship("Game", back_populates="backlog_entries")
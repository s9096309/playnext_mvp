import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.database.schemas import BacklogStatus


Base = declarative_base()


class User(Base):
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
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String, index=True)
    genre = Column(String)
    release_date = Column(Date)
    platform = Column(String)
    igdb_id = Column(Integer, unique=True, index=True)
    igdb_link = Column(String, nullable=True)
    image_url = Column(String)
    age_rating = Column(String)

    backlog_items = relationship("BacklogItem", back_populates="game")
    ratings = relationship("Rating", back_populates="game")


class BacklogItem(Base):
    __tablename__ = "backlog_items"

    backlog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    status = Column(Enum(BacklogStatus, values_callable=lambda obj: [e.value for e in obj], native_enum=False))
    rating = Column(Float, nullable=True)
    added_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    user = relationship("User", back_populates="backlog_items")
    game = relationship("Game", back_populates="backlog_items")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)

    game_id = Column(Integer, ForeignKey("games.game_id"), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC), nullable=False)

    recommendation_reason = Column(String, nullable=False)
    documentation_rating = Column(Float, nullable=False)

    raw_gemini_output = Column(Text, nullable=True)
    structured_json_output = Column(Text, nullable=True)

    user = relationship("User", back_populates="recommendations")
    game = relationship("Game")


class Rating(Base):
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
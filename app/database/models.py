from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

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
    is_admin = Column(Boolean, default=False)  # Add is_admin column

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
    image_url = Column(String)
    age_rating = Column(String)

    backlog_items = relationship("BacklogItem", back_populates="game")
    recommendations = relationship("Recommendation", back_populates="game")
    ratings = relationship("Rating", back_populates="game")

class BacklogStatus(enum.Enum):
    playing = "playing"
    completed = "completed"
    dropped = "dropped"

class BacklogItem(Base):
    __tablename__ = "backlog_items"

    backlog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    status = Column(Enum(BacklogStatus))
    rating = Column(Float)
    play_status = Column(String)

    user = relationship("User", back_populates="backlog_items")
    game = relationship("Game", back_populates="backlog_items")

class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    timestamp = Column(DateTime)
    recommendation_reason = Column(String)
    documentation_rating = Column(Float)

    user = relationship("User", back_populates="recommendations")
    game = relationship("Game", back_populates="recommendations")

class Rating(Base):
    __tablename__ = "ratings"

    rating_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    game_id = Column(Integer, ForeignKey("games.game_id"))
    rating = Column(Float)
    comment = Column(String)
    rating_date = Column(DateTime)

    user = relationship("User", back_populates="ratings")
    game = relationship("Game", back_populates="ratings")
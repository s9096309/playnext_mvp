# app/database/session.py

"""
Database session management and table creation for SQLAlchemy.

This module sets up the database engine, manages database sessions,
and provides a function to create all necessary database tables.
"""

from typing import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

from app.database.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """
    Creates all database tables defined in the Base metadata.

    This function should be called during application startup to
    ensure the database schema is up-to-date.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session for FastAPI routes.

    Yields:
        sqlalchemy.orm.Session: A database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# app/database/session.py

from typing import Generator, Annotated
import os

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

from app.database.models import Base

load_dotenv()

_engine: Engine = None
_SessionLocal: sessionmaker = None

def get_engine() -> Engine:
    """
    Initializes and returns the SQLAlchemy engine.
    This function ensures the engine is created only once.
    """
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not found in .env file or environment.")

        connect_args = {}
        # Apply check_same_thread=False only for SQLite databases
        if database_url.startswith("sqlite:///"):
            connect_args["check_same_thread"] = False

        _engine = create_engine(database_url, connect_args=connect_args)
    return _engine

def get_session_local_factory() -> sessionmaker:
    """
    Initializes and returns the SQLAlchemy sessionmaker factory.
    This function ensures the sessionmaker is created only once.
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def create_tables():
    """
    Creates all database tables defined in the Base metadata.
    This function should be called during application startup to
    ensure the database schema is up-to-date.
    It now uses the lazily initialized engine.
    """
    Base.metadata.create_all(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session for FastAPI routes.
    It now uses the lazily initialized SessionLocal factory.
    Yields:
        sqlalchemy.orm.Session: A database session.
    """
    db = get_session_local_factory()()
    try:
        yield db
    finally:
        db.close()

# Define SessionDep here, after get_db
SessionDep = Annotated[Session, Depends(get_db)]
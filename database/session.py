# app/database/session.py

from typing import Generator, Annotated
import os

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

_engine: Engine = None
_SessionLocal: sessionmaker = None


Base = declarative_base()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            # Build DATABASE_URL from components
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_PORT")
            db = os.getenv("POSTGRES_DB")

            if not all([user, password, host, port, db]):
                raise ValueError("Missing DB connection environment variables")

            database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

        connect_args = {}

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

SessionDep = Annotated[Session, Depends(get_db)]
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from app.database.models import Base, User, Game, BacklogItem, Recommendation, Rating
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to create tables
def create_tables():
    Base.metadata.create_all(bind=engine, tables=[User.__table__, Game.__table__, Rating.__table__, Recommendation.__table__, BacklogItem.__table__])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
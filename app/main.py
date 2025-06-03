# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.database import crud, models
from app.database.session import create_tables, get_db
from app.routers import auth, backlog_items, games, recommendations, users


# Event handler for application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application startup and shutdown events.

    Ensures database tables are created on startup.
    """
    # Create all database tables on startup using the dedicated function
    create_tables()
    print("Database tables created/checked.")
    yield
    # On shutdown, perform any cleanup if necessary
    print("Application shutdown.")


app = FastAPI(
    title="PlayNext API",
    description="API for managing game backlogs, ratings, and recommendations.",
    version="0.1.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS (Cross-Origin Resource Sharing) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, tags=["Auth"])

app.include_router(users.router, tags=["Users"])

app.include_router(games.router, tags=["Games"])
app.include_router(backlog_items.router, tags=["Backlog"])
app.include_router(recommendations.router, tags=["Recommendations"])
"""
Main application entry point for the PlayNext API.

This module initializes the FastAPI application, includes routers,
mounts static files, configures CORS, and handles database table creation
on application startup.
"""

import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path  # Import the Path module

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from database.session import create_tables
from routers import auth, backlog_items, games, recommendations, users, ratings

print("--- PlayNext API application module loaded ---")

# --- ADD THIS ---
# Define the absolute path to the project's root directory
BASE_DIR = Path(__file__).resolve().parent
# --- END ADD ---


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Context manager for application startup and shutdown events.
    """
    print("Application startup complete.")
    yield
    print("Application shutdown.")


# The variable MUST be named 'application' for Elastic Beanstalk's Python platform
application = FastAPI(
    title="PlayNext API",
    description="API for managing game backlogs, ratings, and recommendations.",
    version="0.1.0",
    lifespan=lifespan
)

@application.get("/", summary="Root endpoint for PlayNext API")
async def read_root_message():
    """
    Provides a welcome message for the API root.
    """
    return {"message": "Welcome to the PlayNext API! Navigate to /docs for API documentation."}


# --- MODIFY THIS LINE ---
application.mount("/static", StaticFiles(directory=f"{BASE_DIR}/static"), name="static")
# --- END MODIFY ---


# Configure CORS (Cross-Origin Resource Sharing) middleware
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

application.include_router(auth.router, tags=["Auth"])
application.include_router(users.router, tags=["Users"])
application.include_router(ratings.router, prefix="/users/me/ratings", tags=["Ratings"])
application.include_router(games.router, tags=["Games"])
application.include_router(backlog_items.router, tags=["Backlog"])
application.include_router(recommendations.router, tags=["Recommendations"])


if __name__ == "__main__":
    # This block is for local development
    uvicorn.run(application, host="0.0.0.0", port=8080)
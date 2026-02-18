"""
Main application entry point for the PlayNext API.

This module initializes the FastAPI application, includes routers,
mounts static files, configures CORS, and handles database table creation
on application startup.
"""

import uvicorn
import os
from contextlib import asynccontextmanager
from pathlib import Path

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter


from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from routers import auth, backlog_items, games, recommendations, users, ratings

print("--- PlayNext API application module loaded ---")

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Context manager for application startup and shutdown events.
    """
    print("Application startup complete.")
    yield
    print("Application shutdown.")

# --- SECURITY CONFIGURATION ---
env = os.getenv("PLAYNEXT_ENV", "development")

docs_url = None if env == "production" else "/docs"
redoc_url = None if env == "production" else "/redoc"

print(f"Starting in mode: {env} (Docs enabled: {docs_url is not None})")
# ------------------------------

application = FastAPI(
    title="PlayNext API",
    description="API for managing game backlogs, ratings, and recommendations.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url
)

# --- REGISTER RATE LIMITER---
application.state.limiter = limiter
application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@application.get("/", summary="Serve the frontend")
async def serve_frontend():
    """
    Serves the main HTML file.
    """
    return FileResponse("static/index.html")

application.mount("/static", StaticFiles(directory=f"{BASE_DIR}/static"), name="static")

# Configure CORS Middleware
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
    uvicorn.run(application, host="0.0.0.0", port=8080)
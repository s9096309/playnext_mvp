"""
Main application entry point for the PlayNext API.

This module initializes the FastAPI application, includes routers,
mounts static files, configures CORS, and handles database table creation
on application startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

# NEW IMPORT: Mangum
from mangum import Mangum

from app.database.session import create_tables
from app.routers import auth, backlog_items, games, recommendations, users, ratings

print("--- PlayNext API main module loaded ---")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Context manager for application startup and shutdown events.

    Ensures database tables are created on startup.
    This part will run during a Lambda cold start.
    """
    # Create all database tables on startup using the dedicated function
    create_tables()
    print("Database tables created/checked.")
    yield
    # On shutdown, perform any cleanup if necessary.
    # In Lambda, this shutdown part is less predictable as the environment
    # can be recycled at any time by AWS. For database connections, ensure
    # your session management (e.g., using get_db() in routers) is robust,
    # and consider AWS RDS Proxy for true connection pooling.
    print("Application shutdown.")


app = FastAPI(
    title="PlayNext API",
    description="API for managing game backlogs, ratings, and recommendations.",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/dev"
)

@app.get("/", summary="Root endpoint for PlayNext API")
async def read_root_message():
    """
    Provides a welcome message for the API root.
    """
    return {"message": "Welcome to the PlayNext API! Navigate to /dev/docs for API documentation."}


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

app.include_router(ratings.router, prefix="/users/me/ratings", tags=["Ratings"])

app.include_router(games.router, tags=["Games"])
app.include_router(backlog_items.router, tags=["Backlog"])
app.include_router(recommendations.router, tags=["Recommendations"])


# --- NEW ADDITION FOR AWS LAMBDA ---
# This wraps your FastAPI application with Mangum, making it compatible
# with AWS Lambda's event invocation model.
# When setting up your Lambda function, you will point the "Handler"
# field to this variable (e.g., if this file is 'main.py', the handler
# would be 'main.handler').
handler = Mangum(app)
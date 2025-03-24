from fastapi import FastAPI
from app.routers import users, games, ratings, recommendations, auth

app = FastAPI()

app.include_router(users.router)
app.include_router(games.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"]) # include the auth router.
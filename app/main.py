# main.py
from fastapi import FastAPI
from app.routers import users, games, ratings, recommendations

app = FastAPI()

app.include_router(users.router)
app.include_router(games.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
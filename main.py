from fastapi import FastAPI
from contextlib import asynccontextmanager #import this
from app.database.session import create_tables
from app.routers import users, games, backlog_items, recommendations, ratings

@asynccontextmanager
async def lifespan(app: FastAPI): #add this
    create_tables()
    yield #add this

app = FastAPI(lifespan=lifespan) #update this

app.include_router(users.router)
app.include_router(games.router)
app.include_router(backlog_items.router)
app.include_router(recommendations.router)
app.include_router(ratings.router)
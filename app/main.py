from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from.routers import users, games, ratings, recommendations, auth, backlog_items  # Use relative imports
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(games.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(backlog_items.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
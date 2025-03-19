# app/routers/games.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas
from app.database.session import get_db

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/", response_model=schemas.Game)
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    db_game = crud.get_game(db, game_id=game.igdb_id)
    if db_game:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game already registered")
    return crud.create_game(db=db, game=game)

@router.get("/{game_id}", response_model=schemas.Game)
def read_game(game_id: int, db: Session = Depends(get_db)):
    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return db_game

@router.get("/", response_model=list[schemas.Game])
def read_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    games = crud.get_games(db, skip=skip, limit=limit)
    return games

@router.put("/{game_id}", response_model=schemas.Game)
def update_game(game_id: int, game: schemas.GameUpdate, db: Session = Depends(get_db)):
    db_game = crud.update_game(db, game_id=game_id, game_update=game)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return db_game

@router.delete("/{game_id}", response_model=schemas.Game)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    db_game = crud.delete_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return db_game
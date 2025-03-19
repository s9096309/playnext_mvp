# app/routers/backlog_items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas
from app.database.session import get_db

router = APIRouter(prefix="/backlog_items", tags=["backlog_items"])

@router.post("/", response_model=schemas.BacklogItem)
def create_backlog_item(backlog_item: schemas.BacklogItemCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=backlog_item.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_game = crud.get_game(db, game_id=backlog_item.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_backlog_item(db=db, backlog_item=backlog_item)

@router.get("/{backlog_id}", response_model=schemas.BacklogItem)
def read_backlog_item(backlog_id: int, db: Session = Depends(get_db)):
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")
    return db_backlog_item

@router.get("/", response_model=list[schemas.BacklogItem])
def read_backlog_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    backlog_items = crud.get_backlog_items(db, skip=skip, limit=limit)
    return backlog_items

@router.put("/{backlog_id}", response_model=schemas.BacklogItem)
def update_backlog_item(backlog_id: int, backlog_item: schemas.BacklogItemUpdate, db: Session = Depends(get_db)):
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")

    if backlog_item.user_id is not None:
        db_user = crud.get_user(db, user_id=backlog_item.user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if backlog_item.game_id is not None:
        db_game = crud.get_game(db, game_id=backlog_item.game_id)
        if not db_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_backlog_item(db=db, backlog_id=backlog_id, backlog_item_update=backlog_item)

@router.delete("/{backlog_id}", response_model=schemas.BacklogItem)
def delete_backlog_item(backlog_id: int, db: Session = Depends(get_db)):
    db_backlog_item = crud.delete_backlog_item(db, backlog_id=backlog_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")
    return db_backlog_item
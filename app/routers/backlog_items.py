# app/routers/backlog_items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/backlog", tags=["backlog_items"])

@router.post("/", response_model=schemas.BacklogItem)
def create_backlog_item(backlog_item: schemas.BacklogItemCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=backlog_item.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_game = crud.get_game(db, game_id=backlog_item.game_id)
    if not db_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.create_backlog_item(db=db, backlog_item=backlog_item)

@router.get("/{backlog_item_id}", response_model=schemas.BacklogItem)
def read_backlog_item(
    backlog_item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific backlog item by its ID.
    """
    backlog_item = crud.get_backlog_item(db, backlog_id=backlog_item_id)
    if not backlog_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found"
        )
    return backlog_item

@router.get("/", response_model=list[schemas.BacklogItem])
def read_backlog_items(skip: int = 0, limit: int = 100, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    backlog_items = crud.get_backlog_items(db, skip=skip, limit=limit)
    return backlog_items

@router.put("/{backlog_item_id}", response_model=schemas.BacklogItem)
def update_backlog_item(backlog_item_id: int, backlog_item: schemas.BacklogItemUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_backlog_item = crud.get_backlog_item(db, backlog_id=backlog_item_id)
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

    return crud.update_backlog_item(db=db, backlog_id=backlog_item_id, backlog_item_update=backlog_item)

@router.delete("/{backlog_item_id}", response_model=schemas.BacklogItem)
def delete_backlog_item(backlog_item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_backlog_item = crud.delete_backlog_item(db, backlog_id=backlog_item_id)
    if db_backlog_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backlog item not found")
    return db_backlog_item

@router.get("/user/{user_id}", response_model=list[schemas.BacklogItem])
def read_user_backlog(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the backlog items of a specific user.
    """
    backlog_items = crud.get_user_backlog(db, user_id=user_id)
    if not backlog_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backlog items not found for this user"
        )
    return backlog_items
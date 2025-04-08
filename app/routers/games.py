from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from app.utils import igdb_utils
from typing import Optional, List
from app.utils.auth import get_current_user

router = APIRouter(prefix="/games", tags=["games"])

@router.post("/", response_model=schemas.Game)
def create_game(title: str = Query(..., description="Game title"), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Create a game by title, fetching data from IGDB.
    """
    igdb_games = igdb_utils.search_games_igdb(title)
    if not igdb_games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found on IGDB")

    igdb_game = igdb_games[0]
    igdb_id = igdb_game.get('id')

    db_game = crud.get_game_by_igdb_id(db, igdb_id=igdb_id)
    if db_game:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game already registered")

    image_url = ""
    if 'cover' in igdb_game and igdb_game['cover']:
        cover_data = igdb_utils.get_cover_url(igdb_game['cover']['id'])
        if cover_data:
            image_url = cover_data

    age_rating = None
    if 'age_ratings' in igdb_game and igdb_game['age_ratings']:
        igdb_age_ratings = igdb_game['age_ratings']
        mapped_ratings = [igdb_utils.map_igdb_age_rating(rating['rating']) for rating in igdb_age_ratings]
        valid_ratings = [rating for rating in mapped_ratings if rating is not None]
        if valid_ratings:
            age_rating = max(valid_ratings)
        else:
            age_rating = None

    release_date = "2000-01-01"  # Default date
    if 'release_dates' in igdb_game and igdb_game['release_dates']:
        release_date_str = igdb_game['release_dates'][0].get('human')
        if release_date_str:
            try:
                release_date = datetime.strptime(release_date_str, "%b %d, %Y").date()
            except ValueError:
                print(f"Warning: Could not parse release date: {release_date_str}")

    game_data = schemas.GameCreate(
        game_name=igdb_game.get('name', title),
        genre=", ".join([genre['name'] for genre in igdb_game.get('genres', [])]),
        release_date=release_date,
        platform=", ".join([platform['name'] for platform in igdb_game.get('platforms', [])]),
        igdb_id=igdb_id,
        image_url=image_url,
        age_rating=age_rating,
        user_id = current_user.user_id #add user ID to created game.
    )

    return crud.create_game(db=db, game=game_data)

@router.get("/", response_model=list[schemas.Game])
def read_games(skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, genre: Optional[str] = None, platform: Optional[str] = None, db: Session = Depends(get_db)):
    games = crud.get_games(db, skip=skip, limit=limit, sort_by=sort_by, genre=genre, platform=platform)
    for game in games:
        if game.image_url is None:
            game.image_url = ""
    return games

@router.put("/{game_id}", response_model=schemas.Game)
def update_game(game_id: int, game: schemas.GameUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    if db_game.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this game")
    return crud.update_game(db=db, game_id=game_id, game_update=game)

@router.delete("/{game_id}", response_model=schemas.Game)
def delete_game(game_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    if db_game.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this game")
    return crud.delete_game(db, game_id=game_id)

@router.get("/search/{query}", response_model=List[schemas.Game])
def search_games(query: str, db: Session = Depends(get_db)):
    """
    Search for games, prioritizing the local database and then IGDB,
    and storing IGDB results in the database.
    """
    # 1. Search local database
    db_games = crud.search_games_db(db, query=query)

    if db_games:
        return db_games  # Return local results if found

    # 2. If not found in the local database, search IGDB
    igdb_games = igdb_utils.search_games_igdb(query)
    if not igdb_games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No games found")

    games: List[schemas.Game] = []
    for igdb_game in igdb_games:
        image_url = ""
        if 'cover' in igdb_game and igdb_game['cover']:
            cover_data = igdb_utils.get_cover_url(igdb_game['cover']['id'])
            if cover_data:
                image_url = cover_data.replace("t_thumb", "t_cover_big")

        age_rating = None
        if 'age_ratings' in igdb_game and igdb_game['age_ratings']:
            igdb_age_ratings = igdb_game['age_ratings']
            mapped_ratings = [igdb_utils.map_igdb_age_rating(rating['rating']) for rating in igdb_age_ratings]
            valid_ratings = [rating for rating in mapped_ratings if rating is not None]
            if valid_ratings:
                age_rating = max(valid_ratings)

        release_date = "2000-01-01"
        if 'release_dates' in igdb_game and igdb_game['release_dates']:
            release_date_str = igdb_game['release_dates'][0].get('human')
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%b %d, %Y").date()
                except ValueError:
                    print(f"Warning: Could not parse release date: {release_date_str}")

        game_data = schemas.GameCreate(
            game_name=igdb_game.get('name', ""),
            genre=", ".join([genre['name'] for genre in igdb_game.get('genres', [])]),
            release_date=release_date,
            platform=", ".join([platform['name'] for platform in igdb_game.get('platforms', [])]),
            igdb_id=igdb_game.get('id', 0),
            image_url=image_url,
            age_rating=age_rating,
            user_id=None  # User ID is not relevant for searched games
        )

        # Store the IGDB game in the database if it doesn't exist
        db_game = crud.create_game_if_not_exists(db=db, game=game_data)
        games.append(db_game)

    return games

@router.options("/")
async def games_options(request: Request):
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "file://",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })
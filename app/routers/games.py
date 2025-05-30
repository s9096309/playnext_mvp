# app/routers/games.py

"""
API routes for managing game information.

This module provides endpoints to create, retrieve, update, and delete game entries.
It integrates with the IGDB API to fetch game details during creation and search,
and handles data persistence in the local database.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.database import crud, schemas, models
from app.database.session import get_db
from app.utils import igdb_utils
from app.utils.auth import get_current_user # Assuming admin checks for update/delete


router = APIRouter(prefix="/games", tags=["games"])


def _process_igdb_game_data(igdb_game: dict) -> schemas.GameCreate:
    """
    Helper function to process raw IGDB game data into a GameCreate schema.
    """
    image_url = ""
    if 'cover' in igdb_game and igdb_game['cover']:
        cover_data = igdb_utils.get_cover_url(igdb_game['cover']['id'])
        if cover_data:
            # Standardize image size for consistency
            image_url = cover_data.replace("t_thumb", "t_cover_big")

    age_rating: Optional[str] = None
    if 'age_ratings' in igdb_game and igdb_game['age_ratings']:
        # igdb_age_ratings is a list of objects, each with a 'rating' key
        mapped_ratings = [igdb_utils.map_igdb_age_rating(rating['rating'])
                          for rating in igdb_game['age_ratings']]
        valid_ratings = [rating for rating in mapped_ratings if rating is not None]
        if valid_ratings:
            # Take the highest age rating if multiple are present
            age_rating = max(valid_ratings)

    release_date = datetime(2000, 1, 1).date() # Default date if not found or parse error
    if 'release_dates' in igdb_game and igdb_game['release_dates']:
        # IGDB returns a list of release date objects, take the first one
        release_date_str = igdb_game['release_dates'][0].get('human')
        if release_date_str:
            try:
                # Example: "Dec 03, 2020"
                release_date = datetime.strptime(release_date_str, "%b %d, %Y").date()
            except ValueError:
                # Fallback to default if parsing fails
                print(f"Warning: Could not parse release date for {igdb_game.get('name')}: {release_date_str}")

    return schemas.GameCreate(
        game_name=igdb_game.get('name', "Unknown Game"), # Provide a fallback name
        genre=", ".join([genre['name'] for genre in igdb_game.get('genres', [])]),
        release_date=release_date,
        platform=", ".join([platform['name'] for platform in igdb_game.get('platforms', [])]),
        igdb_id=igdb_game.get('id', 0), # Ensure default for igdb_id
        image_url=image_url,
        age_rating=age_rating,
    )


@router.post("/", response_model=schemas.Game, status_code=status.HTTP_201_CREATED)
def create_game(
    title: str = Query(..., description="Title of the game to add from IGDB"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new game entry in the database by searching IGDB.

    Searches IGDB for the given game title, retrieves its details,
    and adds it to the local database. If the game already exists
    or is not found on IGDB, appropriate HTTP exceptions are raised.
    This operation requires administrator privileges.

    Args:
        title (str): The title of the game to search for on IGDB.
        current_user (models.User): The authenticated user. Must be an administrator.
        db (Session): The database session.

    Returns:
        schemas.Game: The newly created game object.

    Raises:
        HTTPException:
            - 403 Forbidden: If the current user is not an administrator.
            - 404 Not Found: If the game is not found on IGDB.
            - 400 Bad Request: If the game is already registered in the database.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can add new games."
        )

    igdb_games = igdb_utils.search_games_igdb(title)
    if not igdb_games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found on IGDB")

    # Take the first and most relevant result from IGDB search
    igdb_game_data = igdb_games[0]
    igdb_id = igdb_game_data.get('id')

    db_game = crud.get_game_by_igdb_id(db, igdb_id=igdb_id)
    if db_game:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Game already registered")

    game_data = _process_igdb_game_data(igdb_game_data)
    return crud.create_game(db=db, game=game_data)


@router.get("/", response_model=List[schemas.Game])
def read_games(
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = Query(None, description="Sort games by 'game_name', 'release_date', or 'age_rating'"),
    genre: Optional[str] = Query(None, description="Filter games by genre"),
    platform: Optional[str] = Query(None, description="Filter games by platform"),
    db: Session = Depends(get_db)
    # REMOVED: current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves a list of games with optional filtering and pagination.
    This endpoint is publicly accessible.

    Args:
        skip (int): The number of records to skip (for pagination).
        limit (int): The maximum number of records to return.
        sort_by (Optional[str]): Field to sort the games by ('game_name', 'release_date', 'age_rating').
        genre (Optional[str]): Filter games by a specific genre.
        platform (Optional[str]): Filter games by a specific platform.
        db (Session): The database session.

    Returns:
        List[schemas.Game]: A list of game objects.
    """
    # Ensure image_url is not None for response model consistency
    games = crud.get_games(db, skip=skip, limit=limit, sort_by=sort_by, genre=genre, platform=platform)
    for game in games:
        if game.image_url is None:
            game.image_url = ""
    return games

@router.put("/{game_id}", response_model=schemas.Game)
def update_game(
    game_id: int,
    game_update: schemas.GameUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing game's details.

    This operation requires administrator privileges.

    Args:
        game_id (int): The ID of the game to update.
        game_update (schemas.GameUpdate): The updated game data.
        current_user (models.User): The authenticated user. Must be an administrator.
        db (Session): The database session.

    Returns:
        schemas.Game: The updated game object.

    Raises:
        HTTPException:
            - 403 Forbidden: If the current user is not an administrator.
            - 404 Not Found: If the game is not found.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update games."
        )

    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.update_game(db=db, game_id=game_id, game_update=game_update)


@router.delete("/{game_id}", response_model=schemas.Game, status_code=status.HTTP_200_OK)
def delete_game(
    game_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a game from the database.

    This operation requires administrator privileges.

    Args:
        game_id (int): The ID of the game to delete.
        current_user (models.User): The authenticated user. Must be an administrator.
        db (Session): The database session.

    Returns:
        schemas.Game: The deleted game object.

    Raises:
        HTTPException:
            - 403 Forbidden: If the current user is not an administrator.
            - 404 Not Found: If the game is not found.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete games."
        )

    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    return crud.delete_game(db, game_id=game_id)


@router.get("/search/{query_str}", response_model=List[schemas.Game])
def search_games(
    query_str: str,
    db: Session = Depends(get_db)
):
    """
    Searches for games in the database and, if not found, falls back to IGDB.

    Games found on IGDB but not in the local database will be added automatically.

    Args:
        query_str (str): The search query (game title).
        db (Session): The database session.

    Returns:
        List[schemas.Game]: A list of game objects matching the query.

    Raises:
        HTTPException: 404 Not Found: If no games are found locally or on IGDB.
    """
    db_games = crud.search_games_db(db, query=query_str)

    if db_games:
        return db_games

    # If not found in DB, search IGDB and add to DB
    igdb_games = igdb_utils.search_games_igdb(query_str)
    if not igdb_games:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No games found locally or on IGDB")

    games: List[schemas.Game] = []
    for igdb_game in igdb_games:
        game_data = _process_igdb_game_data(igdb_game)
        # This function creates if not exists and returns the DB object
        db_game = crud.create_game_if_not_exists(db=db, game=game_data)
        games.append(db_game)

    return games


@router.options("/")
async def games_options(request: Request): # pylint: disable=W0613
    """
    Handles OPTIONS requests for the /games/ endpoint.

    This is typically used for CORS preflight requests by web browsers.

    Args:
        request (Request): The incoming FastAPI request object.

    Returns:
        Response: An HTTP 200 OK response with appropriate CORS headers.
    """
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*", # Changed to allow all for development. Adjust for production.
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    })

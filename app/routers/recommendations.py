import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import crud, models, schemas, user_crud
from app.database.session import get_db

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

RECOMMENDATION_CACHE_DURATION_HOURS = 24


async def generate_recommendations_gemini(prompt: str) -> str:
    """
    Generates game recommendations using the Gemini API.

    Args:
        prompt (str): The prompt string to send to the Gemini model.

    Returns:
        str: The raw text response from the Gemini model.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text


@router.get("/user", response_model=schemas.RecommendationResponse)
async def get_user_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    force_generate: bool = Query(
        False,
        description="Set to true to force new recommendations generation, "
                    "bypassing cache."
    )
):
    """
    Generates personalized game recommendations for a user.

    This endpoint gathers data about a user's ratings and backlog to
    construct a prompt for the Gemini AI model, which then provides
    game recommendations. The response includes structured recommendations
    and the raw Gemini output.

    Args:
        user_id (int): The ID of the user for whom to generate
                       recommendations.
        db (Session): The database session.
        force_generate (bool): If True, bypasses cache and forces new
                               generation.

    Returns:
        schemas.RecommendationResponse: An object containing structured
                                        recommendations and the raw Gemini
                                        response.

    Raises:
        HTTPException: If the user is not found or recommendation generation
                       fails.
    """
    db_user = user_crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not force_generate:
        latest_cached_reco = crud.get_latest_user_recommendation(db, user_id)
        if latest_cached_reco:
            cached_timestamp_utc = (
                latest_cached_reco.generation_timestamp.replace(tzinfo=timezone.utc)
            )
            current_time_utc = datetime.now(timezone.utc)

            if ((current_time_utc - cached_timestamp_utc) <
                    timedelta(hours=RECOMMENDATION_CACHE_DURATION_HOURS)):
                print(
                    f"Returning cached recommendations for user {user_id}. "
                    f"Cache age: {current_time_utc - cached_timestamp_utc}"
                )
                try:
                    cached_recommendations_data = json.loads(
                        latest_cached_reco.structured_json_output
                    )
                    structured_recommendations = [
                        schemas.StructuredRecommendation(**item)
                        for item in cached_recommendations_data
                    ]
                    return schemas.RecommendationResponse(
                        structured_recommendations=structured_recommendations,
                        gemini_response=latest_cached_reco.raw_gemini_output
                    )
                except json.JSONDecodeError as e:
                    print(f"Error parsing cached JSON for user {user_id}: {e}. "
                          "Regenerating.")
                except Exception as e:
                    print(f"Unexpected error with cached recommendations for "
                          f"user {user_id}: {e}. Regenerating.")

    print(f"Generating new recommendations for user {user_id} "
          f"(cache expired, not found, or force_generate was true).")
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    backlog_items = crud.get_user_backlog(db, user_id=user_id)

    favorite_game_ids: List[int] = []
    disliked_game_ids: List[int] = []

    game_ratings_avg: dict[int, float] = {}
    for rating_obj in ratings:
        if rating_obj.game_id not in game_ratings_avg:
            game_ratings_avg[rating_obj.game_id] = []
        game_ratings_avg[rating_obj.game_id].append(rating_obj.rating)

    for game_id, ratings_list in game_ratings_avg.items():
        avg_rating = sum(ratings_list) / len(ratings_list)
        if avg_rating >= 8.0:
            favorite_game_ids.append(game_id)
        elif avg_rating <= 4.0:
            disliked_game_ids.append(game_id)

    for item in backlog_items:
        if (item.status == schemas.BacklogStatus.COMPLETED or
                item.status == schemas.BacklogStatus.PLAYING):
            if item.game_id not in favorite_game_ids:
                favorite_game_ids.append(item.game_id)
        elif item.status == schemas.BacklogStatus.DROPPED:
            if item.game_id not in disliked_game_ids:
                disliked_game_ids.append(item.game_id)
        if item.rating:
            if item.rating >= 8.0 and item.game_id not in favorite_game_ids:
                favorite_game_ids.append(item.game_id)
            elif item.rating <= 4.0 and item.game_id not in disliked_game_ids:
                disliked_game_ids.append(item.game_id)

    unique_favorite_game_ids = list(set(favorite_game_ids))
    unique_disliked_game_ids = list(set(disliked_game_ids))

    favorite_game_names = [
        game_obj.game_name
        for game_id in unique_favorite_game_ids
        if (game_obj := crud.get_game(db, game_id=game_id)) is not None
    ]
    disliked_game_names = [
        game_obj.game_name
        for game_id in unique_disliked_game_ids
        if (game_obj := crud.get_game(db, game_id=game_id)) is not None
    ]
    backlog_game_names = [
        game_obj.game_name
        for item in backlog_items
        if (game_obj := crud.get_game(db, game_id=item.game_id)) is not None
    ]

    favorite_games_string = (", ".join(favorite_game_names)
                             if favorite_game_names else
                             "no specific favorite games")
    disliked_games_string = (", ".join(disliked_game_names)
                             if disliked_game_names else
                             "no specific disliked games")
    backlog_string = (", ".join(backlog_game_names)
                      if backlog_game_names else
                      "no games in their backlog")

    prompt = f"""
    The user's favorite games are: {favorite_games_string}.
    The user's backlog contains: {backlog_string}.
    The user dislikes: {disliked_games_string}.

    Based on the user's preferences, recommend 3 games.
    For each recommendation, include:
    - "name": The game's name.
    - "genre": A primary genre for the game.
    - "igdb_link": A direct link to the game on IGDB (e.g., "https://www.igdb.com/games/game-name").
    - "reasoning": A short, clear reason why this game is recommended based on the user's preferences.

    Provide the recommendations in a JSON array format. Ensure the response is valid JSON and can be parsed directly.
    Example:
    ```json
    [
      {{
        "name": "Game Title 1",
        "genre": "RPG",
        "igdb_link": "[https://www.igdb.com/games/game-title-1](https://www.igdb.com/games/game-title-1)",
        "reasoning": "Because you enjoyed similar RPGs like X and Y."
      }},
      {{
        "name": "Game Title 2",
        "genre": "Action-Adventure",
        "igdb_link": "[https://www.igdb.com/games/game-title-2](https://www.igdb.com/games/game-title-2)",
        "reasoning": "You like open-world games and this has a similar exploration style to Z."
      }}
    ]
    ```
    """

    gemini_response = await generate_recommendations_gemini(prompt)

    structured_recommendations: List[schemas.StructuredRecommendation] = []
    extracted_json_str: Optional[str] = None

    try:
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', gemini_response)
        if json_match:
            extracted_json_str = json_match.group(1)
            recommendations_data = json.loads(extracted_json_str)

            if isinstance(recommendations_data, list):
                for item in recommendations_data:
                    game_name = item.get("name") or item.get("title")
                    genre = item.get("genre")
                    igdb_link = item.get("igdb_link")
                    reasoning = item.get("reasoning")

                    if all([game_name, genre, igdb_link, reasoning]):
                        structured_recommendations.append(
                            schemas.StructuredRecommendation(
                                game_name=game_name,
                                genre=genre,
                                igdb_link=igdb_link,
                                reasoning=reasoning
                            )
                        )
                    else:
                        print(f"Skipping incomplete recommendation: {item}")
            else:
                print("Gemini response JSON is not a list, expected a list "
                      "of recommendations.")
        else:
            print("No JSON code block (```json...```) found in Gemini response.")

    except json.JSONDecodeError as e:
        print(f"Gemini response is not valid JSON: {e}")
        print(f"Raw response: {gemini_response}")
    except Exception as e:
        print(f"An unexpected error occurred during processing Gemini response: "
              f"{e}")

    if extracted_json_str:
        new_recommendation = schemas.RecommendationCreate(
            user_id=user_id,
            raw_gemini_output=gemini_response,
            structured_json_output=extracted_json_str,
            generation_timestamp=datetime.now(timezone.utc)
        )
        crud.create_recommendation(db, new_recommendation)

    return schemas.RecommendationResponse(
        structured_recommendations=structured_recommendations,
        gemini_response=gemini_response
    )
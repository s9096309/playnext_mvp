import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import crud, models, schemas, user_crud
from app.database.session import get_db
from app.utils import igdb_utils


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

RECOMMENDATION_CACHE_DURATION_HOURS = 24


async def generate_recommendations_gemini(prompt: str) -> str:
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
                latest_cached_reco.timestamp.replace(tzinfo=timezone.utc)
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
    - "reasoning": A short, clear reason why this game is recommended based on the user's preferences.

    IMPORTANT: Do NOT include 'igdb_link' or 'igdb_id' in the JSON from Gemini.
    I will fetch the IGDB link, ID, and cover URL myself using the game 'name'.

    Provide the recommendations in a JSON array format. Ensure the response is valid JSON and can be parsed directly.
    Example:
    ```json
    [
      {{
        "name": "Game Title 1",
        "genre": "RPG",
        "reasoning": "Because you enjoyed similar RPGs like X and Y."
      }},
      {{
        "name": "Game Title 2",
        "genre": "Action-Adventure",
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
                    genre_from_gemini = item.get("genre")

                    if game_name:
                        igdb_search_results = igdb_utils.search_games_igdb(game_name)

                        igdb_game_data = None
                        if igdb_search_results and len(igdb_search_results) > 0:
                            first_igdb_game = igdb_search_results[0]

                            igdb_id = first_igdb_game.get("id")
                            igdb_link = first_igdb_game.get("url")
                            igdb_genres = [g['name']
                                           for g in first_igdb_game.get('genres', [])]
                            final_genre = (", ".join(igdb_genres)
                                           if igdb_genres else genre_from_gemini)

                            cover_url = None
                            if first_igdb_game.get('cover') and \
                                    first_igdb_game['cover'].get('url'):
                                raw_cover_url = first_igdb_game['cover']['url']
                                if raw_cover_url.startswith('//'):
                                    cover_url = 'https:' + raw_cover_url
                                else:
                                    cover_url = raw_cover_url
                                cover_url = cover_url.replace('t_thumb', 't_cover_big')

                            if igdb_id and igdb_link:
                                igdb_game_data = {
                                    "igdb_id": igdb_id,
                                    "name": first_igdb_game.get("name"),
                                    "url": igdb_link,
                                    "genre": final_genre,
                                    "cover_url": cover_url
                                }

                        if igdb_game_data:
                            reasoning = item.get("reasoning")
                            final_game_name = igdb_game_data["name"]

                            db_game = crud.get_game_by_igdb_id(
                                db, igdb_id=igdb_game_data["igdb_id"]
                            )
                            if not db_game:
                                new_game_data = schemas.GameCreate(
                                    game_name=final_game_name,
                                    igdb_id=igdb_game_data["igdb_id"],
                                    genre=igdb_game_data.get("genre"),
                                    igdb_link=igdb_game_data.get("url"),
                                    image_url=igdb_game_data.get("cover_url"),
                                )
                                db_game = crud.create_game(db, game=new_game_data)
                                print(f"Created new game in DB: {final_game_name} "
                                      f"(ID: {igdb_game_data['igdb_id']})")

                            if db_game:
                                structured_recommendations.append(
                                    schemas.StructuredRecommendation(
                                        game_name=db_game.game_name,
                                        genre=db_game.genre,
                                        igdb_link=db_game.igdb_link,
                                        reasoning=reasoning
                                    )
                                )

                                new_recommendation_entry = schemas.RecommendationCreate(
                                    user_id=user_id,
                                    game_id=db_game.game_id,
                                    timestamp=datetime.now(timezone.utc),
                                    recommendation_reason=reasoning,
                                    documentation_rating=5.0,
                                    raw_gemini_output=gemini_response,
                                    structured_json_output=extracted_json_str
                                )
                                crud.create_recommendation(db, new_recommendation_entry)
                                print(f"Saved recommendation for game: {db_game.game_name}")
                            else:
                                print("Could not find or create game for recommendation: "
                                      f"{final_game_name}. Skipping saving to DB.")
                        else:
                            print(f"No IGDB data found for game '{game_name}' from "
                                  "Gemini. Skipping this recommendation.")
                    else:
                        print(f"Skipping incomplete recommendation from Gemini: {item}. "
                              "Game name missing.")
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

    return schemas.RecommendationResponse(
        structured_recommendations=structured_recommendations,
        gemini_response=gemini_response
    )
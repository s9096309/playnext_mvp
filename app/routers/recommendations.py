# app/routers/recommendations.py

"""
API routes for generating game recommendations.

This module provides an endpoint to fetch personalized game recommendations
for a user, leveraging the Gemini AI model and user interaction data.
"""

import json
import os
import re
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import crud, models, schemas
from app.database.session import get_db

load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


async def generate_recommendations_gemini(prompt: str) -> str:
    """
    Generates game recommendations using the Gemini API.

    Args:
        prompt (str): The prompt string to send to the Gemini model.

    Returns:
        str: The raw text response from the Gemini model.
    """
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return response.text


@router.post("/user", response_model=schemas.RecommendationResponse)
async def get_user_recommendations(
    user_id: int, # Directly accept user_id
    db: Session = Depends(get_db)
):
    """
    Generates personalized game recommendations for a user.

    This endpoint gathers data about a user's ratings and backlog to
    construct a prompt for the Gemini AI model, which then provides
    game recommendations. The response includes structured recommendations
    and the raw Gemini output.

    Args:
        user_id (int): The ID of the user for whom to generate recommendations.
        db (Session): The database session.

    Returns:
        schemas.RecommendationResponse: An object containing structured
                                        recommendations and the raw Gemini response.

    Raises:
        HTTPException: If the user is not found.
    """
    # Verify user exists
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Fetch user data
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    backlog_items = crud.get_user_backlog(db, user_id=user_id)

    favorite_game_ids: List[int] = []
    disliked_game_ids: List[int] = []

    # Process ratings
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

    # Process backlog items and consolidate game IDs
    # Add games from backlog (completed/playing) to favorites if not already there
    for item in backlog_items:
        if (item.status == schemas.BacklogStatus.COMPLETED or
                item.status == schemas.BacklogStatus.PLAYING):
            if item.game_id not in favorite_game_ids:
                favorite_game_ids.append(item.game_id)
        elif item.status == schemas.BacklogStatus.DROPPED:
            if item.game_id not in disliked_game_ids:
                disliked_game_ids.append(item.game_id)
        if item.rating: # Consider rating from backlog item as well
            if item.rating >= 8.0 and item.game_id not in favorite_game_ids:
                favorite_game_ids.append(item.game_id)
            elif item.rating <= 4.0 and item.game_id not in disliked_game_ids:
                disliked_game_ids.append(item.game_id)

    # Ensure unique IDs and fetch game names safely
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

    # Create strings for prompt, handling empty lists
    favorite_games_string = ", ".join(favorite_game_names) if favorite_game_names else "no specific favorite games"
    disliked_games_string = ", ".join(disliked_game_names) if disliked_game_names else "no specific disliked games"
    backlog_string = ", ".join(backlog_game_names) if backlog_game_names else "no games in their backlog"

    # Construct prompt for Gemini
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

    # Generate recommendations
    gemini_response = await generate_recommendations_gemini(prompt)

    structured_recommendations: List[schemas.StructuredRecommendation] = []

    try:
        # Extract JSON from Gemini response using regex
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', gemini_response)
        if json_match:
            json_str = json_match.group(1)
            recommendations_data = json.loads(json_str)

            if isinstance(recommendations_data, list):
                for item in recommendations_data:
                    # Use .get() with a default of None to prevent KeyError
                    game_name = item.get("name") or item.get("title")
                    genre = item.get("genre")
                    igdb_link = item.get("igdb_link")
                    reasoning = item.get("reasoning")

                    # Only append if essential fields are present
                    if all([game_name, genre, igdb_link, reasoning]):
                        structured_recommendations.append(schemas.StructuredRecommendation(
                            game_name=game_name,
                            genre=genre,
                            igdb_link=igdb_link,
                            reasoning=reasoning
                        ))
                    else:
                        print(f"Skipping incomplete recommendation: {item}")
            else:
                print("Gemini response JSON is not a list, expected a list of recommendations.")
        else:
            print("No JSON code block (```json...```) found in Gemini response.")

    except json.JSONDecodeError as e:
        print(f"Gemini response is not valid JSON: {e}")
        print(f"Raw response: {gemini_response}")
    except Exception as e:
        print(f"An unexpected error occurred during processing Gemini response: {e}")

    return schemas.RecommendationResponse(
        structured_recommendations=structured_recommendations,
        gemini_response=gemini_response
    )
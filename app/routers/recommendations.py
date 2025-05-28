from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from typing import List
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_recommendations_gemini(prompt: str):
    """Generates recommendations using Gemini API (asynchronously)."""
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return response.text

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/user", response_model=schemas.RecommendationResponse)
async def get_user_recommendations(user_request: schemas.UserRequest, db: Session = Depends(get_db)):
    """Generates game recommendations using the Gemini API, considering user ratings, backlog, and comments."""
    user_id = user_request.user_id

    # Fetch user data
    ratings = crud.get_ratings_by_user(db, user_id=user_id)
    backlog_items = crud.get_user_backlog_items(db, user_id=user_id)

    favorite_games = []
    disliked_games = []

    # Process ratings
    game_ratings = {}
    for rating in ratings:
        if rating.game_id not in game_ratings:
            game_ratings[rating.game_id] = []
        game_ratings[rating.game_id].append(rating.rating)

    for game_id, game_ratings_list in game_ratings.items():
        avg_rating = sum(game_ratings_list) / len(game_ratings_list)
        if avg_rating >= 8.0:
            favorite_games.append(game_id)
        elif avg_rating <= 4.0:
            disliked_games.append(game_id)

    # Process backlog items
    for item in backlog_items:
        if item.status == schemas.BacklogStatus.completed or item.status == schemas.BacklogStatus.playing:
            if item.game_id not in favorite_games:
                favorite_games.append(item.game_id)
        elif item.status == schemas.BacklogStatus.dropped:
            if item.game_id not in disliked_games:
                disliked_games.append(item.game_id)
        if item.rating:
            if item.rating >= 8.0 and item.game_id not in favorite_games:
                favorite_games.append(item.game_id)
            elif item.rating <= 4.0 and item.game_id not in disliked_games:
                disliked_games.append(item.game_id)

    # Create strings for prompt
    favorite_games_string = ", ".join([crud.get_game(db, game_id=game_id).game_name for game_id in favorite_games if crud.get_game(db, game_id=game_id)])
    disliked_games_string = ", ".join([crud.get_game(db, game_id=game_id).game_name for game_id in disliked_games if crud.get_game(db, game_id=game_id)])
    backlog_game_names = [crud.get_game(db, game_id=item.game_id).game_name for item in backlog_items if crud.get_game(db, game_id=item.game_id)]
    backlog_string = ", ".join(backlog_game_names) if backlog_game_names else "None"

    # Construct prompt
    prompt = f"""
    The user's favorite games are: {favorite_games_string}.
    The user's backlog contains: {backlog_string}.
    The user dislikes: {disliked_games_string}.

    Based on the user's preferences, recommend 3 games, including genre, igdb link, and a short reasoning, in JSON format.
    Ensure the response is valid JSON and can be parsed directly.
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
                    game_name = item.get("name") or item.get("title")  # Check for both "name" and "title"
                    genre = item.get("genre")
                    igdb_link = item.get("igdb_link")
                    reasoning = item.get("reasoning")

                    structured_recommendations.append(schemas.StructuredRecommendation(
                        game_name=game_name,
                        genre=genre,
                        igdb_link=igdb_link,
                        reasoning=reasoning
                    ))
            else:
                print("Gemini response is not a list.")
        else:
            print("No JSON found in Gemini response.")

    except json.JSONDecodeError:
        print("Gemini response is not valid JSON.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return schemas.RecommendationResponse(
        structured_recommendations=structured_recommendations,
        gemini_response=gemini_response
    )

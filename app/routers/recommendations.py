import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from app.utils.auth import get_current_user
from app.recommendations_utils import cosine_similarity
from typing import List
from datetime import datetime
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

class UserIDRequest(BaseModel):
    user_id: int

@router.post("/generate", response_model=List[schemas.Game])
def generate_recommendations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Generates game recommendations for the current user based on collaborative filtering."""

    # Get the user's ratings
    user_ratings = crud.get_ratings_by_user(db, user_id=current_user.user_id)

    # Get a list of all users.
    all_users = crud.get_users(db)

    # Create a dictionary to store user similarities.
    user_similarities = {}

    # Calculate user similarities.
    for other_user in all_users:
        if other_user.user_id != current_user.user_id:
            other_user_ratings = crud.get_ratings_by_user(db, user_id=other_user.user_id)
            # calculate similarity here. This example will just use the amount of shared ratings.
            shared_ratings = 0
            for user_rating in user_ratings:
                for other_user_rating in other_user_ratings:
                    if user_rating.game_id == other_user_rating.game_id:
                        shared_ratings += 1
            user_similarities[other_user.user_id] = shared_ratings

    # Get games rated by similar users.
    recommended_game_ids = set()
    for other_user_id, similarity in user_similarities.items():
        if similarity > 0:  # only use users with shared ratings.
            other_user_ratings = crud.get_ratings_by_user(db, user_id=other_user_id)
            for other_user_rating in other_user_ratings:
                recommended_game_ids.add(other_user_rating.game_id)

    # Get the game objects from the database.
    recommended_games = []
    for game_id in recommended_game_ids:
        game = crud.get_game(db, game_id=game_id)
        if game:
            recommended_games.append(game)

    return recommended_games

def create_user_profile(liked_games, db: Session):
    """Creates a user profile based on liked games' attributes."""
    user_profile = {}
    for game_id in liked_games:
        game = crud.get_game(db, game_id=game_id)
        if game:
            if game.genre:
                for genre in game.genre.split(", "):
                    user_profile[genre] = user_profile.get(genre, 0) + 1
            if game.platform:
                for platform in game.platform.split(", "):
                    user_profile[platform] = user_profile.get(platform, 0) + 1
            if game.age_rating:
                user_profile[game.age_rating] = user_profile.get(game.age_rating, 0) + 1
            if game.release_date:
                user_profile[str(game.release_date.year)] = user_profile.get(str(game.release_date.year), 0) + 1
    return user_profile

@router.post("/content", response_model=List[schemas.Game])
def generate_content_based_recommendations(liked_games: List[int], db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> List[schemas.Game]:
    """Generates content-based recommendations for the current user."""
    user_profile = create_user_profile(liked_games, db)
    all_games = crud.get_games(db)
    game_similarities = []

    for game in all_games:
        game_vector = {}
        if game.genre:
            for genre in game.genre.split(", "):
                game_vector[genre] = 1
        if game.platform:
            for platform in game.platform.split(", "):
                game_vector[platform] = 1
        if game.age_rating:
            game_vector[game.age_rating] = 1
        if game.release_date:
            game_vector[str(game.release_date.year)] = 1

        similarity = cosine_similarity(user_profile, game_vector)
        game_similarities.append((game, similarity))

    recommended_games = [game for game, similarity in sorted(game_similarities, key=lambda x: x[1], reverse=True)]
    return recommended_games[:10]

@router.get("/user/{user_id}", response_model=List[schemas.Game])
def get_user_recommendations(user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get recommendations for a specific user.
    """
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view recommendations for this user."
        )

    user_ratings = crud.get_ratings_by_user(db, user_id=user_id)
    if not user_ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ratings found for this user.")

    # Generate recommendations logic here (using existing functions)
    recommended_games = generate_recommendations(db, current_user)

    return recommended_games

@router.post("/gemini")
def get_gemini_recommendations(request: UserIDRequest, db: Session = Depends(get_db)):
    user_id = request.user_id
    user_ratings = crud.get_ratings_with_comments_by_user(db, user_id=user_id)
    user_backlog = crud.get_user_backlog(db, user_id=user_id)

    prompt = "Recommend 3 video games for user with the following preferences:\n"
    if user_ratings:
        prompt += "High Ratings: "
        for rating in user_ratings:
            prompt += f"{rating.game.game_name} ({rating.rating} stars)"
            if rating.comment:
                prompt += f" Comments: {rating.comment}"
            prompt += ", "
        prompt = prompt[:-2] + "\n"
    if user_backlog:
        prompt += f"Backlog: {[item.game.game_name for item in user_backlog]}\n"

    recommendations_text = generate_recommendations_gemini(prompt)

    # Return the full Gemini AI API response
    return {"gemini_response": recommendations_text}


def generate_recommendations_gemini(prompt: str):
    model = genai.GenerativeModel('gemini-1.5-pro-latest') #change the model name.
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Gemini API Error"

def parse_recommendations_gemini(recommendations_text: str):
    recommendations = []
    lines = recommendations_text.split('\n')
    for line in lines:
        if ". **" in line: #check for the start of a recommendation.
            parts = line.split(". **")
            if len(parts) == 2:
                game_name = parts[1].split(':**')[0]
                recommendations.append({"game_name": game_name, "genre": "Various"}) #genre is not reliably provided.
    return recommendations

@router.post("/test")
def test_endpoint(request: UserIDRequest): #use request model
    return {"user_id": request.user_id}
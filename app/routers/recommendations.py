from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from app.recommendations_utils import get_igdb_game_data

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

class UserIDRequest(BaseModel):
    user_id: int

def generate_recommendations_gemini(prompt: str):
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return response.text

def parse_recommendations_gemini(recommendations_text: str):
    recommendations = []
    lines = recommendations_text.split('\n')
    for line in lines:
        if ". **" in line:
            parts = line.split(". **")
            if len(parts) == 2:
                game_name = parts[1].split(':**')[0]
                recommendations.append({"game_name": game_name, "genre": "Various"})
    return recommendations

@router.post("/test")
def test_recommendations():
    return {"message": "Recommendations endpoint is working"}

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

    recommendations = parse_recommendations_gemini(recommendations_text)

    detailed_recommendations = []
    for recommendation in recommendations:
        game = crud.get_game_by_name(db, game_name=recommendation['game_name'])
        if game:
            igdb_data = get_igdb_game_data(game.igdb_id)
            igdb_link = f"https://www.igdb.com/games/{igdb_data[0].get('slug', '')}" if igdb_data else None
            detailed_recommendations.append({
                "game_name": recommendation['game_name'],
                "genre": recommendation['genre'],
                "igdb_link": igdb_link,
            })
        else:
            # Game not found, add it to the database
            # Attempt to get data from IGDB
            try:
                # search by name, and return the first result.
                igdb_search_data = crud.search_igdb_game(game_name = recommendation['game_name'])
                if igdb_search_data:
                    game_data = igdb_search_data[0]
                    release_date = datetime.fromtimestamp(game_data.get('first_release_date', 0)).date() if game_data.get('first_release_date') else None
                    age_rating = str(game_data.get('age_ratings', [{}])[0].get('rating')) if game_data.get('age_ratings') else None

                    new_game = schemas.GameCreate(
                        game_name=game_data.get('name', recommendation['game_name']),
                        genre=", ".join([g.get('name') for g in game_data.get('genres', [])]) if game_data.get('genres') else recommendation['genre'],
                        release_date=release_date,
                        platform=", ".join([p.get('name') for p in game_data.get('platforms', [])]) if game_data.get('platforms') else None,
                        igdb_id=game_data.get('id'),
                        image_url=f"https://images.igdb.com/igdb/image/upload/t_cover_big/{game_data.get('cover', {}).get('image_id')}.jpg" if game_data.get('cover', {}).get('image_id') else None,
                        age_rating=age_rating,
                    )
                    game = crud.create_game(db, game=new_game)
                    igdb_link = f"https://www.igdb.com/games/{game_data.get('slug', '')}" if game_data.get('slug') else None
                    detailed_recommendations.append({
                        "game_name": recommendation['game_name'],
                        "genre": recommendation['genre'],
                        "igdb_link": igdb_link,
                    })
                else:
                    detailed_recommendations.append({
                        "game_name": recommendation['game_name'],
                        "genre": recommendation['genre'],
                        "igdb_link": None,
                    })
                    print(f"Game '{recommendation['game_name']}' not found in IGDB. Skipping recommendation.")

            except Exception as e:
                print(f"Error adding game '{recommendation['game_name']}': {e}")
                detailed_recommendations.append({
                    "game_name": recommendation['game_name'],
                    "genre": recommendation['genre'],
                    "igdb_link": None,
                })

    return {"structured_recommendations": detailed_recommendations, "gemini_response": recommendations_text}
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import crud, schemas, models
from app.database.session import get_db
from app.recommendations_utils import (
    cosine_similarity,
    pearson_correlation,
    calculate_user_similarities,
    create_item_user_matrix,
    calculate_item_similarity,
)
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

def generate_recommendations_task(db: Session):
    """
    Background task to generate recommendations.
    """
    try:
        ratings = crud.get_ratings(db)
        if not ratings:
            print("No ratings found, cannot generate recommendations.")
            return

        user_ratings = {}
        for rating in ratings:
            if rating.user_id not in user_ratings:
                user_ratings[rating.user_id] = {}
            user_ratings[rating.user_id][rating.game_id] = rating.rating

        similarity_function = cosine_similarity

        user_similarities = calculate_user_similarities(user_ratings, similarity_function)

        for user_id, similarities in user_similarities.items():
            sorted_similarities = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
            for other_user_id, similarity_score in sorted_similarities[:10]:
                if other_user_id != user_id:
                    other_user_ratings = user_ratings.get(other_user_id, {})
                    user_rated_games = user_ratings.get(user_id, {}).keys()
                    for game_id, rating in other_user_ratings.items():
                        if game_id not in user_rated_games:
                            recommendation = schemas.RecommendationCreate(
                                user_id=user_id,
                                game_id=game_id,
                                timestamp=datetime.now(),
                                recommendation_reason="Recommended based on similar user",
                                documentation_rating=similarity_score,
                            )
                            db_recommendation = models.Recommendation(**recommendation.dict())
                            db.add(db_recommendation)
        db.commit()

    except Exception as e:
        print(f"Error generating recommendations: {e}")

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_recommendations(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger the generation of new recommendations.
    """
    background_tasks.add_task(generate_recommendations_task, db)
    return {"message": "Recommendation generation triggered"}

@router.get("/user_similarity/{similarity_metric}")
def get_user_similarity(similarity_metric: str, db: Session = Depends(get_db)):
    """Calculates and returns user similarities."""
    ratings = crud.get_ratings(db)
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found")

    user_ratings = {}
    for rating in ratings:
        if rating.user_id not in user_ratings:
            user_ratings[rating.user_id] = {}
        user_ratings[rating.user_id][rating.game_id] = rating.rating

    if similarity_metric == "cosine":
        similarity_function = cosine_similarity
    elif similarity_metric == "pearson":
        similarity_function = pearson_correlation
    else:
        raise HTTPException(status_code=400, detail="Invalid similarity metric")

    similarities = calculate_user_similarities(user_ratings, similarity_function)

    return similarities

@router.get("/item_similarity")
def get_item_similarity(db: Session = Depends(get_db)):
    """Calculates and returns item similarities."""
    ratings = crud.get_ratings(db)
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found")

    item_user_matrix = create_item_user_matrix(ratings)
    item_similarities = calculate_item_similarity(item_user_matrix)

    return item_similarities
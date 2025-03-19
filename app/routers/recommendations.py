from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import crud, schemas
from app.database.session import get_db
from app.recommendations_utils import cosine_similarity, pearson_correlation, calculate_user_similarities

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/user_similarity/{similarity_metric}")
def get_user_similarity(similarity_metric: str, db: Session = Depends(get_db)):
    """Calculates and returns user similarities."""

    # 1. Fetch rating data from the database
    ratings = crud.get_ratings(db) #assuming you have a crud function to get all ratings.
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found")

    user_ratings = {}
    for rating in ratings:
        if rating.user_id not in user_ratings:
            user_ratings[rating.user_id] = {}
        user_ratings[rating.user_id][rating.game_id] = rating.rating

    # 3. Choose the similarity function
    if similarity_metric == "cosine":
        similarity_function = cosine_similarity
    elif similarity_metric == "pearson":
        similarity_function = pearson_correlation
    else:
        raise HTTPException(status_code=400, detail="Invalid similarity metric")

    # 4. Calculate similarities
    similarities = calculate_user_similarities(user_ratings, similarity_function)

    return similarities
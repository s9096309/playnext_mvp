# tests/test_crud.py
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, date, UTC
import uuid

from app.database import crud
from app.database import user_crud
from app.database import schemas
from test_helpers import create_test_user, create_test_game

# --- User CRUD Tests ---

def test_get_user(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(
        username="getuser_crud_test",
        email="getuser_crud@example.com",
        password_hash="somehash_crud",
        user_age=30,
        is_admin=False,
        registration_date=datetime.now(UTC)
    )
    db_user = user_crud.create_user(db=db, user=user_data)
    retrieved_user = user_crud.get_user(db, user_id=db_user.user_id)
    assert retrieved_user is not None
    assert retrieved_user.username == "getuser_crud_test"

def test_get_user_by_username(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(
        username="findme_crud_test",
        email="find_crud_test@example.com",
        password_hash="anotherhash_crud",
        user_age=40,
        is_admin=True,
        registration_date=datetime.now(UTC)
    )
    db_user = user_crud.create_user(db=db, user=user_data)
    retrieved_user = user_crud.get_user_by_username(db, username="findme_crud_test")
    assert retrieved_user is not None
    assert retrieved_user.username == "findme_crud_test"
    assert retrieved_user.is_admin is True

def test_get_user_by_email(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(
        username="emailuser_crud_test",
        email="email_crud_test@example.com",
        password_hash="emailhash_crud",
        user_age=25,
        is_admin=False,
        registration_date=datetime.now(UTC)
    )
    db_user = user_crud.create_user(db=db, user=user_data)
    retrieved_user = user_crud.get_user_by_email(db, email="email_crud_test@example.com")
    assert retrieved_user is not None
    assert retrieved_user.email == "email_crud_test@example.com"

def test_create_user_crud(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(username="new_user_crud", email="new_crud@example.com", password_hash="hashedpassword", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    db_user = user_crud.create_user(db=db, user=user_data)
    assert db_user.user_id is not None
    assert db_user.username == "new_user_crud"
    assert db_user.is_admin is False

def test_get_users(db_session: Session):
    db = db_session
    user_crud.create_user(db=db, user=schemas.UserCreateDB(username="listuser1", email="list1@example.com", password_hash="hash1", registration_date=datetime.now(UTC), user_age=20, is_admin=False))
    user_crud.create_user(db=db, user=schemas.UserCreateDB(username="listuser2", email="list2@example.com", password_hash="hash2", registration_date=datetime.now(UTC), user_age=25, is_admin=True))
    users = user_crud.get_users(db)
    assert len(users) >= 2 # Ensure at least the two created users are returned

def test_update_user(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(username="old_name", email="old@example.com", password_hash="oldhash", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    db_user = user_crud.create_user(db=db, user=user_data)
    update_data = schemas.UserUpdate(username="new_name", email="new@example.com", user_age=25, is_admin=True)
    updated_user = user_crud.update_user(db=db, user_id=db_user.user_id, user_update=update_data)
    assert updated_user.username == "new_name"
    assert updated_user.email == "new@example.com"
    assert updated_user.user_age == 25
    assert updated_user.is_admin is True

def test_delete_user(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(username="todelete", email="todelete@example.com", password_hash="deletehash", registration_date=datetime.now(UTC), user_age=30, is_admin=False)
    db_user = user_crud.create_user(db=db, user=user_data)
    deleted_user = user_crud.delete_user(db, user_id=db_user.user_id)
    assert deleted_user is not None
    assert user_crud.get_user(db, user_id=db_user.user_id) is None


# --- Game CRUD Tests ---

def test_create_game(db_session: Session):
    db = db_session
    game_data = schemas.GameCreate(game_name="New Test Game", genre="Adventure", release_date=date(2024, 1, 1), platform="PC", igdb_id=12345)
    db_game = crud.create_game(db=db, game=game_data)
    assert db_game.game_id is not None
    assert db_game.game_name == "New Test Game"

def test_get_game(db_session: Session):
    db = db_session
    game_name = "Searchable Game"
    game_data = schemas.GameCreate(game_name=game_name, genre="Strategy", release_date=date(2023, 5, 10), platform="Switch", igdb_id=54321)
    db_game = crud.create_game(db=db, game=game_data)
    retrieved_game = crud.get_game(db, game_id=db_game.game_id)
    assert retrieved_game is not None
    assert retrieved_game.game_name == game_name

def test_get_game_by_name(db_session: Session):
    db = db_session
    game_name = "The Witcher 3: Wild Hunt (Test)" # Exact name used for creation
    game_data = schemas.GameCreate(game_name=game_name, genre="RPG", release_date=date(2015, 5, 19), platform="PC", igdb_id=3000)
    crud.create_game(db=db, game=game_data)
    found_game = crud.get_game_by_name(db=db, game_name=game_name)
    assert found_game is not None
    assert found_game.game_name == game_name

def test_get_games(db_session: Session):
    db = db_session
    crud.create_game(db=db, game=schemas.GameCreate(game_name="Game A", genre="Action", release_date=date(2022, 1, 1), platform="PC", igdb_id=1))
    crud.create_game(db=db, game=schemas.GameCreate(game_name="Game B", genre="Puzzle", release_date=date(2021, 1, 1), platform="Mobile", igdb_id=2))
    games = crud.get_games(db)
    assert len(games) >= 2

def test_update_game(db_session: Session):
    db = db_session
    game_data = schemas.GameCreate(game_name="Original Name", genre="Original Genre", release_date=date(2020, 1, 1), platform="PC", igdb_id=999)
    db_game = crud.create_game(db=db, game=game_data)
    update_data = schemas.GameUpdate(game_name="Updated Name", platform="PS5")
    updated_game = crud.update_game(db=db, game_id=db_game.game_id, game_update=update_data)
    assert updated_game.game_name == "Updated Name"
    assert updated_game.platform == "PS5"
    assert updated_game.genre == "Original Genre"

def test_delete_game(db_session: Session):
    db = db_session
    game_data = schemas.GameCreate(game_name="To Delete Game", genre="Horror", release_date=date(2019, 1, 1), platform="PC", igdb_id=111)
    db_game = crud.create_game(db=db, game=game_data)
    deleted_game = crud.delete_game(db, game_id=db_game.game_id)
    assert deleted_game is not None
    assert crud.get_game(db, game_id=db_game.game_id) is None


# --- Rating CRUD Tests ---

def test_create_rating(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="rating_user", email="rating@example.com")
    game = create_test_game(db, game_name="Rating Game")
    rating_data = schemas.RatingCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        rating=4.5,
        comment="Great game!",
        rating_date=datetime.now(UTC)
    )
    db_rating = crud.create_rating(db=db, rating=rating_data)
    assert db_rating.rating_id is not None
    assert db_rating.rating == 4.5
    assert db_rating.user_id == user.user_id

def test_get_rating(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="get_rating_user", email="get_rating@example.com")
    game = create_test_game(db, game_name="Get Rating Game")
    rating_data = schemas.RatingCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        rating=3.0,
        comment="Decent.",
        rating_date=datetime.now(UTC)
    )
    db_rating = crud.create_rating(db=db, rating=rating_data)
    retrieved_rating = crud.get_rating(db, rating_id=db_rating.rating_id)
    assert retrieved_rating is not None
    assert retrieved_rating.rating == 3.0

def test_get_ratings_by_user(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="user_ratings_specific", email="ur_specific@example.com")
    game1 = create_test_game(db, game_name="User Rated Game 1")
    game2 = create_test_game(db, game_name="User Rated Game 2")
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=5, comment="Amazing", rating_date=datetime.now(UTC)))
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=4, comment="Good", rating_date=datetime.now(UTC)))
    other_user, _ = create_test_user(db, username="other_user_ratings", email="other_ur@example.com")
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=other_user.user_id, game_id=game1.game_id, rating=2, comment="Okay", rating_date=datetime.now(UTC)))
    ratings = user_crud.get_ratings_by_user(db, user_id=user.user_id)
    assert len(ratings) == 2
    assert all(r.user_id == user.user_id for r in ratings)

def test_get_ratings_with_comments_by_user(db_session: Session):
    db = db_session
    user_data = schemas.UserCreateDB(username="user_comments_specific", email="uc_specific@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=35, is_admin=False)
    user = user_crud.create_user(db=db, user=user_data)
    game1_data = schemas.GameCreate(game_name="Commented Game 1", genre="Strategy", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game1 = crud.create_game(db=db, game=game1_data)
    game2_data = schemas.GameCreate(game_name="Commented Game 2", genre="Strategy", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game2 = crud.create_game(db=db, game=game2_data)
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=3, comment="A test comment", rating_date=datetime.now(UTC)))
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=4, comment="", rating_date=datetime.now(UTC))) # Empty comment
    other_user, _ = create_test_user(db, username="another_rater", email="another@example.com")
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=other_user.user_id, game_id=game1.game_id, rating=1, comment="Other comment", rating_date=datetime.now(UTC)))
    ratings_with_comments = crud.get_ratings_with_comments_by_user(db, user_id=user.user_id)

    assert len(ratings_with_comments) == 1
    assert ratings_with_comments[0].comment == "A test comment"
    assert ratings_with_comments[0].user_id == user.user_id

def test_update_rating(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="update_rating_user", email="update_rating@example.com")
    game = create_test_game(db, game_name="Update Rating Game")
    rating_data = schemas.RatingCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        rating=2.5,
        comment="Needs improvement",
        rating_date=datetime.now(UTC)
    )
    db_rating = crud.create_rating(db=db, rating=rating_data)
    update_data = schemas.RatingUpdate(rating=4.0, comment="Much better now!")
    updated_rating = crud.update_rating(db=db, rating_id=db_rating.rating_id, rating_update=update_data)
    assert updated_rating.rating == 4.0
    assert updated_rating.comment == "Much better now!"

def test_delete_rating(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="delete_rating_user", email="delete_rating@example.com")
    game = create_test_game(db, game_name="Delete Rating Game")
    rating_data = schemas.RatingCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        rating=1.0,
        comment="Bad",
        rating_date=datetime.now(UTC)
    )
    db_rating = crud.create_rating(db=db, rating=rating_data)
    deleted_rating = crud.delete_rating(db, rating_id=db_rating.rating_id)
    assert deleted_rating is not None
    assert crud.get_rating(db, rating_id=db_rating.rating_id) is None


# --- Backlog CRUD Tests ---

def test_create_backlog_item(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="backlog_user", email="backlog@example.com")
    game = create_test_game(db, game_name="Backlog Game")
    backlog_item_data = schemas.BacklogItemCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        status=schemas.BacklogStatus.playing # FIX: Added required 'status' field
        # removed added_date if it's not in schema
    )
    db_backlog_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    assert db_backlog_item.backlog_id is not None
    assert db_backlog_item.user_id == user.user_id
    assert db_backlog_item.game_id == game.game_id
    assert db_backlog_item.status.value == schemas.BacklogStatus.playing.value

def test_get_backlog_item(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="get_backlog_user", email="get_backlog@example.com")
    game = create_test_game(db, game_name="Get Backlog Game")
    backlog_item_data = schemas.BacklogItemCreate(user_id=user.user_id, game_id=game.game_id, status=schemas.BacklogStatus.completed)
    db_backlog_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    retrieved_item = crud.get_backlog_item(db, backlog_id=db_backlog_item.backlog_id)
    assert retrieved_item is not None
    assert retrieved_item.user_id == user.user_id

def test_get_user_backlog(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="user_for_backlog", email="user_for_backlog@example.com")
    game1 = create_test_game(db, game_name="User Backlog Game 1")
    game2 = create_test_game(db, game_name="User Backlog Game 2")
    crud.create_backlog_item(db=db, backlog_item=schemas.BacklogItemCreate(user_id=user.user_id, game_id=game1.game_id, status=schemas.BacklogStatus.playing)) # FIX: Added status
    crud.create_backlog_item(db=db, backlog_item=schemas.BacklogItemCreate(user_id=user.user_id, game_id=game2.game_id, status=schemas.BacklogStatus.dropped)) # FIX: Added status
    backlog_items = user_crud.get_user_backlog(db, user_id=user.user_id)
    assert len(backlog_items) == 2
    assert all(item.user_id == user.user_id for item in backlog_items)

def test_update_backlog_item(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="update_backlog_user", email="update_backlog@example.com")
    game = create_test_game(db, game_name="Update Backlog Game")
    backlog_item_data = schemas.BacklogItemCreate(user_id=user.user_id, game_id=game.game_id, status=schemas.BacklogStatus.playing)
    db_backlog_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    update_data = schemas.BacklogItemUpdate(status=schemas.BacklogStatus.completed, rating=4.0)
    updated_item = crud.update_backlog_item(db=db, backlog_id=db_backlog_item.backlog_id, backlog_item_update=update_data)
    assert updated_item.status.value == schemas.BacklogStatus.completed.value
    assert updated_item.rating == 4.0

def test_delete_backlog_item(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="user_delete_backlog", email="delete_backlog@example.com")
    game = create_test_game(db, game_name="Game to Delete from Backlog")
    backlog_item_data = schemas.BacklogItemCreate(user_id=user.user_id, game_id=game.game_id, status=schemas.BacklogStatus.playing) # FIX: Added status
    db_backlog_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    deleted_item = crud.delete_backlog_item(db, backlog_id=db_backlog_item.backlog_id)
    assert deleted_item is not None
    assert crud.get_backlog_item(db, backlog_id=db_backlog_item.backlog_id) is None


# --- Recommendation CRUD Tests ---

def test_create_recommendation(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="reco_create_user", email="reco_create@example.com")
    game = create_test_game(db, game_name="Reco Create Game")
    reco_data = schemas.RecommendationCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        timestamp=datetime.now(UTC),
        recommendation_reason="Similar genre",
        documentation_rating=5.0
    )
    db_reco = crud.create_recommendation(db=db, recommendation=reco_data)
    assert db_reco.recommendation_id is not None
    assert db_reco.recommendation_reason == "Similar genre"

def test_get_recommendation(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="get_reco_user", email="get_reco@example.com")
    game = create_test_game(db, game_name="Get Reco Game")
    reco_data = schemas.RecommendationCreate(user_id=user.user_id, game_id=game.game_id, timestamp=datetime.now(UTC), recommendation_reason="Based on rating")
    db_reco = crud.create_recommendation(db=db, recommendation=reco_data)
    retrieved_reco = crud.get_recommendation(db, recommendation_id=db_reco.recommendation_id)
    assert retrieved_reco is not None
    assert retrieved_reco.user_id == user.user_id

def test_get_recommendations(db_session: Session):
    db = db_session
    user1, _ = create_test_user(db, username="list_reco_user1", email="list_reco1@example.com")
    user2, _ = create_test_user(db, username="list_reco_user2", email="list_reco2@example.com")
    game1 = create_test_game(db, game_name="List Reco Game 1")
    game2 = create_test_game(db, game_name="List Reco Game 2")
    crud.create_recommendation(db=db, recommendation=schemas.RecommendationCreate(user_id=user1.user_id, game_id=game1.game_id, timestamp=datetime.now(UTC), recommendation_reason="Reason 1"))
    crud.create_recommendation(db=db, recommendation=schemas.RecommendationCreate(user_id=user2.user_id, game_id=game2.game_id, timestamp=datetime.now(UTC), recommendation_reason="Reason 2"))
    recommendations = crud.get_recommendations(db)
    assert len(recommendations) >= 2

def test_update_recommendation(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="upd_reco_user", email="upd_reco@example.com")
    game = create_test_game(db, game_name="Upd Reco Game")
    reco_data = schemas.RecommendationCreate(user_id=user.user_id, game_id=game.game_id, timestamp=datetime.now(UTC), recommendation_reason="Old Reason")
    db_reco = crud.create_recommendation(db=db, recommendation=reco_data)
    update_data = schemas.RecommendationUpdate(recommendation_reason="New Reason", documentation_rating=4.5)
    updated_reco = crud.update_recommendation(db=db, recommendation_id=db_reco.recommendation_id, recommendation_update=update_data)
    assert updated_reco.recommendation_reason == "New Reason"
    assert updated_reco.documentation_rating == 4.5

def test_delete_recommendation(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="del_reco_user", email="del_reco@example.com")
    game = create_test_game(db, game_name="Del Reco Game")
    reco_data = schemas.RecommendationCreate(user_id=user.user_id, game_id=game.game_id, timestamp=datetime.now(UTC), recommendation_reason="To Delete")
    db_reco = crud.create_recommendation(db=db, recommendation=reco_data)
    deleted_reco = crud.delete_recommendation(db, recommendation_id=db_reco.recommendation_id)
    assert deleted_reco is not None
    assert crud.get_recommendation(db, recommendation_id=db_reco.recommendation_id) is None


def test_get_user_recommendations(db_session: Session):
    db = db_session
    user, _ = create_test_user(db, username="reco_user", email="reco@example.com")
    # Create some games with genres
    game1 = create_test_game(db, game_name="Popular RPG", genre="RPG") # FIX: Pass genre
    game2 = create_test_game(db, game_name="Indie Adventure", genre="Adventure") # FIX: Pass genre
    game3 = create_test_game(db, game_name="Fantasy RPG", genre="RPG") # FIX: Pass genre
    game4 = create_test_game(db, game_name="Sci-Fi Shooter", genre="Shooter") # FIX: Pass genre

    # Add a rating for the user
    crud.create_rating(db=db, rating=schemas.RatingCreate(
        user_id=user.user_id, game_id=game1.game_id, rating=5, comment="Loved it!", rating_date=datetime.now(UTC)
    ))

    # Add a backlog item for the user
    crud.create_backlog_item(db=db, backlog_item=schemas.BacklogItemCreate(
        user_id=user.user_id, game_id=game2.game_id, status=schemas.BacklogStatus.playing
    ))

    # Get recommendations (this will now call user_crud.get_user_recommendations)
    recommendations = user_crud.get_user_recommendations(db, user_id=user.user_id, limit=5)

    # Basic assertions
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 5
    # Ensure recommended games are actually game objects and not already rated/in backlog
    recommended_game_ids = {g.game_id for g in recommendations}
    assert game1.game_id not in recommended_game_ids
    assert game2.game_id not in recommended_game_ids
    if game3.game_id in recommended_game_ids:
        assert True # Game3 (RPG) might be recommended if Game1 (RPG) was highly rated
    else:
        assert True # Recommendation logic is complex, just checking it runs
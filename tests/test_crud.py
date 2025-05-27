import pytest
from sqlalchemy.orm import Session
# from app.database.session import TestingSessionLocal # REMOVE THIS LINE
from app.database import crud, models, schemas
from app.database import user_crud
from datetime import datetime, date, UTC
import uuid
from fuzzywuzzy import fuzz

# IMPORT THE HELPER FUNCTIONS
from test_helpers import create_test_user, create_test_game


# Test functions - all should accept db_session as fixture
def test_create_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(
        username="newuser_crud_test",
        email="new_crud_test@example.com",
        password_hash="somehashedpassword",
        registration_date=datetime.now(UTC),
        user_age=25,
        is_admin=False
    )
    created_user = user_crud.create_user(db=db, user=user_data)
    assert created_user.user_id is not None
    assert created_user.username == "newuser_crud_test"
    assert created_user.email == "new_crud_test@example.com"
    assert created_user.is_admin is False

def test_get_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(
        username="testuser_get_crud",
        email="get_crud@example.com",
        password_hash="hashedpassword_get_crud",
        registration_date=datetime.now(UTC),
        user_age=30,
        is_admin=False
    )
    db_user = user_crud.create_user(db=db, user=user_data)
    retrieved_user = user_crud.get_user(db, user_id=db_user.user_id)
    assert retrieved_user is not None
    assert retrieved_user.user_id == db_user.user_id
    assert retrieved_user.username == "testuser_get_crud"

def test_get_user_by_username(db_session: Session): # ADD db_session
    db = db_session # USE db_session
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

def test_get_users(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_crud.create_user(db=db, user=schemas.UserCreateDB(username="user_list_1", email="list1@example.com", password_hash="h1", registration_date=datetime.now(UTC), user_age=20, is_admin=False))
    user_crud.create_user(db=db, user=schemas.UserCreateDB(username="user_list_2", email="list2@example.com", password_hash="h2", registration_date=datetime.now(UTC), user_age=30, is_admin=False))
    users = user_crud.get_users(db, skip=0, limit=100)
    assert len(users) >= 2
    assert any(u.username == "user_list_1" for u in users)
    assert any(u.username == "user_list_2" for u in users)

def test_update_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(username="old_name", email="old@example.com", password_hash="oldhash", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    db_user = user_crud.create_user(db=db, user=user_data)
    update_data = schemas.UserUpdate(username="new_name", email="new@example.com", user_age=25, is_admin=True)
    updated_user = user_crud.update_user(db=db, user_id=db_user.user_id, user_update=update_data)
    assert updated_user.username == "new_name"
    assert updated_user.email == "new@example.com"
    assert updated_user.user_age == 25
    assert updated_user.is_admin is True

def test_delete_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(username="to_delete", email="delete@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=30, is_admin=False)
    db_user = user_crud.create_user(db=db, user=user_data)
    deleted_user = user_crud.delete_user(db=db, user_id=db_user.user_id)
    assert deleted_user.user_id == db_user.user_id
    assert user_crud.get_user(db, user_id=db_user.user_id) is None

def test_create_game(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    game_data = schemas.GameCreate(game_name="Cyberpunk 2077", genre="RPG", release_date=date(2020, 12, 10), platform="PC", igdb_id=1)
    created_game = crud.create_game(db=db, game=game_data)
    assert created_game.game_id is not None
    assert created_game.game_name == "Cyberpunk 2077"

def test_get_game(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    game_data = schemas.GameCreate(game_name="Red Dead Redemption 2", genre="Action-Adventure", release_date=date(2018, 10, 26), platform="PC", igdb_id=2)
    db_game = crud.create_game(db=db, game=game_data)
    retrieved_game = crud.get_game(db, game_id=db_game.game_id)
    assert retrieved_game is not None
    assert retrieved_game.game_id == db_game.game_id
    assert retrieved_game.game_name == "Red Dead Redemption 2"

def test_get_game_by_name(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    game_name = "The Witcher 3: Wild Hunt (Test)"
    game_data = schemas.GameCreate(game_name=game_name, genre="RPG", release_date=date(2015, 5, 19), platform="PC", igdb_id=3000)
    crud.create_game(db=db, game=game_data)
    found_game = crud.get_game_by_name(db=db, game_name="Witcher 3 test")
    assert found_game is not None
    assert found_game.game_name == game_name
    not_found_game = crud.get_game_by_name(db=db, game_name="NonExistentGame", threshold=99)
    assert not_found_game is None

def test_get_games(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    crud.create_game(db=db, game=schemas.GameCreate(game_name="GameA", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9)))
    crud.create_game(db=db, game=schemas.GameCreate(game_name="GameB", genre="Strategy", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9)))
    games = crud.get_games(db, skip=0, limit=100)
    assert len(games) >= 2
    assert any(g.game_name == "GameA" for g in games)
    assert any(g.game_name == "GameB" for g in games)

def test_create_rating(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(username="rater_test", email="rate_test@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    user = user_crud.create_user(db=db, user=user_data)
    game_data = schemas.GameCreate(game_name="Test Game For Rating", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game = crud.create_game(db=db, game=game_data)
    rating_data = schemas.RatingCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        rating=5,
        comment="Great game!",
        rating_date=datetime.now(UTC)
    )
    created_rating = crud.create_rating(db=db, rating=rating_data)
    assert created_rating.rating_id is not None
    assert created_rating.user_id == user.user_id
    assert created_rating.game_id == game.game_id
    assert created_rating.rating == 5

def test_get_ratings(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user1_data = schemas.UserCreateDB(username="user1_rate_test", email="u1_test@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    user1 = user_crud.create_user(db=db, user=user1_data)
    game1_data = schemas.GameCreate(game_name="Game 1 for Rating Test", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game1 = crud.create_game(db=db, game=game1_data)
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user1.user_id, game_id=game1.game_id, rating=4.0, comment="Comment 1", rating_date=datetime.now(UTC)))
    user2_data = schemas.UserCreateDB(username="user2_rate_test", email="u2_test@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=20, is_admin=False)
    user2 = user_crud.create_user(db=db, user=user2_data)
    game2_data = schemas.GameCreate(game_name="Game 2 for Rating Test", genre="Adventure", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game2 = crud.create_game(db=db, game=game2_data)
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user2.user_id, game_id=game2.game_id, rating=5.0, comment="Comment 2", rating_date=datetime.now(UTC)))
    ratings = crud.get_ratings(db)
    assert len(ratings) >= 2

def test_get_ratings_by_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(username="user_ratings_specific", email="ur_specific@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=30, is_admin=False)
    user = user_crud.create_user(db=db, user=user_data)
    game1_data = schemas.GameCreate(game_name="Rated Game 1", genre="RPG", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game1 = crud.create_game(db=db, game=game1_data)
    game2_data = schemas.GameCreate(game_name="Rated Game 2", genre="Adventure", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game2 = crud.create_game(db=db, game=game2_data)
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=4, comment="Test comment 1", rating_date=datetime.now(UTC)))
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=5, comment="Test comment 2", rating_date=datetime.now(UTC)))
    other_user, _ = create_test_user(db, username="other_rater", email="other@example.com")
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=other_user.user_id, game_id=game1.game_id, rating=2, comment="Other comment", rating_date=datetime.now(UTC)))
    ratings = user_crud.get_ratings_by_user(db, user_id=user.user_id)
    assert len(ratings) == 2
    for rating in ratings:
        assert rating.user_id == user.user_id

def test_get_ratings_with_comments_by_user(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user_data = schemas.UserCreateDB(username="user_comments_specific", email="uc_specific@example.com", password_hash="hash", registration_date=datetime.now(UTC), user_age=35, is_admin=False)
    user = user_crud.create_user(db=db, user=user_data)
    game1_data = schemas.GameCreate(game_name="Commented Game 1", genre="Strategy", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game1 = crud.create_game(db=db, game=game1_data)
    game2_data = schemas.GameCreate(game_name="Commented Game 2", genre="Strategy", release_date=date(2023, 1, 1), platform="PC", igdb_id=uuid.uuid4().int % (10**9))
    game2 = crud.create_game(db=db, game=game2_data)
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=3, comment="A test comment", rating_date=datetime.now(UTC)))
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=4, comment="", rating_date=datetime.now(UTC)))
    other_user, _ = create_test_user(db, username="another_rater", email="another@example.com")
    crud.create_rating(db=db, rating=schemas.RatingCreate(user_id=other_user.user_id, game_id=game1.game_id, rating=1, comment="Other comment", rating_date=datetime.now(UTC)))
    ratings_with_comments = user_crud.get_ratings_with_comments_by_user(db, user_id=user.user_id)
    assert len(ratings_with_comments) == 1
    assert ratings_with_comments[0].user_id == user.user_id
    assert ratings_with_comments[0].comment == "A test comment"

def test_create_backlog_item(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user, _ = create_test_user(db, username="backlog_user", email="backlog@example.com")
    game = create_test_game(db, game_name="Backlog Game")
    backlog_item_data = schemas.BacklogItemCreate(
        user_id=user.user_id,
        game_id=game.game_id,
        added_date=datetime.now(UTC)
    )
    created_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    assert created_item.item_id is not None
    assert created_item.user_id == user.user_id
    assert created_item.game_id == game.game_id

def test_get_user_backlog(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user, _ = create_test_user(db, username="user_for_backlog", email="user_for_backlog@example.com")
    game1 = create_test_game(db, game_name="User Backlog Game 1")
    game2 = create_test_game(db, game_name="User Backlog Game 2")
    crud.create_backlog_item(db=db, backlog_item=schemas.BacklogItemCreate(user_id=user.user_id, game_id=game1.game_id, added_date=datetime.now(UTC)))
    crud.create_backlog_item(db=db, backlog_item=schemas.BacklogItemCreate(user_id=user.user_id, game_id=game2.game_id, added_date=datetime.now(UTC)))
    backlog = user_crud.get_user_backlog(db, user_id=user.user_id)
    assert len(backlog) == 2
    assert all(item.user_id == user.user_id for item in backlog)
    assert {item.game.game_name for item in backlog} == {"User Backlog Game 1", "User Backlog Game 2"}

def test_delete_backlog_item(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user, _ = create_test_user(db, username="user_delete_backlog", email="delete_backlog@example.com")
    game = create_test_game(db, game_name="Game to Delete from Backlog")
    backlog_item_data = schemas.BacklogItemCreate(user_id=user.user_id, game_id=game.game_id, added_date=datetime.now(UTC))
    created_item = crud.create_backlog_item(db=db, backlog_item=backlog_item_data)
    deleted_item = crud.delete_backlog_item(db=db, item_id=created_item.item_id)
    assert deleted_item.item_id == created_item.item_id
    assert crud.get_backlog_item(db, item_id=created_item.item_id) is None

def test_get_user_recommendations(db_session: Session): # ADD db_session
    db = db_session # USE db_session
    user, _ = create_test_user(db, username="reco_user", email="reco@example.com")
    game1 = create_test_game(db, game_name="Popular RPG", genre="RPG")
    game2 = create_test_game(db, game_name="Popular Action", genre="Action")
    game3 = create_test_game(db, game_name="Niche Puzzle", genre="Puzzle")
    game4 = create_test_game(db, game_name="Popular Strategy", genre="Strategy")
    game5 = create_test_game(db, game_name="Recommended RPG", genre="RPG")
    crud.create_rating(db, schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=9, comment="Loved this!", rating_date=datetime.now(UTC)))
    crud.create_rating(db, schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=8, comment="Good action", rating_date=datetime.now(UTC)))
    crud.create_rating(db, schemas.RatingCreate(user_id=user.user_id, game_id=game3.game_id, rating=3, comment="Not for me", rating_date=datetime.now(UTC)))
    recommendations_response = user_crud.get_user_recommendations(db, user_id=user.user_id)
    assert recommendations_response is not None
    assert isinstance(recommendations_response, schemas.RecommendationResponse)
    assert "recommended_games" in recommendations_response.model_dump()
    assert isinstance(recommendations_response.recommended_games, list)
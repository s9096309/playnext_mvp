from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import crud, models, schemas
from app.database.session import Base
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from fuzzywuzzy import fuzz  # Make sure fuzzywuzzy is installed
import pytest

# Set up an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_user():
    db = TestingSessionLocal()
    user_data = schemas.UserCreateDB(
        username="newuser",
        email="new@example.com",
        password_hash="somehash",
        registration_date=datetime.utcnow(),
        user_age=25,
        is_admin=False
    )
    created_user = crud.create_user(db=db, user=user_data)
    assert created_user is not None
    assert created_user.username == "newuser"
    assert created_user.email == "new@example.com"
    assert created_user.user_age == 25
    assert not created_user.is_admin
    db.close()

def test_get_user():
    db = TestingSessionLocal()
    # Create a test user
    test_user_data = schemas.UserCreateDB(
        username="testuser",
        email="test@example.com",
        password_hash="hashedpassword",
        registration_date=datetime.utcnow(),
        user_age=30,
        is_admin=False
    )
    db_user = models.User(**test_user_data.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Retrieve the user using the crud function
    retrieved_user = crud.get_user(db, user_id=db_user.user_id)

    # Assert that the retrieved user matches the created user
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.user_age == 30
    db.close()


def test_get_user_by_username():
    db = TestingSessionLocal()
    # Create a test user
    test_user_data = schemas.UserCreateDB(
        username="findme",
        email="find@example.com",
        password_hash="anotherhash",
        user_age=40,
        is_admin=True,
        registration_date=datetime.utcnow()
    )
    db_user = models.User(**test_user_data.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    print(f"Created db_user.is_admin: {db_user.is_admin}")

    # Retrieve the user by username
    retrieved_user = crud.get_user_by_username(db, username="findme")

    print(f"Retrieved user.is_admin: {retrieved_user.is_admin if retrieved_user else None}")

    # Assert the retrieved user is correct
    assert retrieved_user is not None
    assert retrieved_user.email == "find@example.com"
    assert retrieved_user.user_age == 40
    assert retrieved_user.is_admin
    db.close()

def test_create_game():
    db = TestingSessionLocal()
    game_data = schemas.GameCreate(
        game_name="Test Game",
        genre="Action",
        release_date=date(2024, 1, 15),
        platform="PC",
        igdb_id=12345,
        image_url="http://example.com/image.jpg",
        age_rating="Teen"
    )
    created_game = crud.create_game(db=db, game=game_data)
    assert created_game is not None
    assert created_game.game_name == "Test Game"
    assert created_game.genre == "Action"
    assert created_game.igdb_id == 12345
    db.close()

def test_get_game():
    db = TestingSessionLocal()
    # Create a test game
    test_game_data = schemas.GameCreate(
        game_name="Another Game",
        genre="RPG",
        release_date=date(2023, 12, 20),
        platform="PS5",
        igdb_id=67890,
        image_url="http://another.com/image.png",
        age_rating="Mature"
    )
    db_game = models.Game(**test_game_data.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)

    # Retrieve the game by ID
    retrieved_game = crud.get_game(db, game_id=db_game.game_id)

    # Assert the retrieved game matches
    assert retrieved_game is not None
    assert retrieved_game.game_name == "Another Game"
    assert retrieved_game.platform == "PS5"
    assert retrieved_game.igdb_id == 67890
    db.close()

def test_get_games():
    db = TestingSessionLocal()
    # Create some test games
    game_data_1 = schemas.GameCreate(game_name="Game A", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=11)
    game_data_2 = schemas.GameCreate(game_name="Game B", genre="RPG", release_date=date(2023, 2, 1), platform="PS5", igdb_id=12)
    crud.create_game(db=db, game=game_data_1)
    crud.create_game(db=db, game=game_data_2)

    games = crud.get_games(db=db)
    assert len(games) >= 2
    assert any(game.game_name == "Game A" for game in games)
    assert any(game.genre == "RPG" for game in games)
    db.close()

def test_get_game_by_name():
    db = TestingSessionLocal()
    game_data = schemas.GameCreate(game_name="The Witcher 3: Wild Hunt", genre="RPG", release_date=date(2015, 5, 19), platform="PC", igdb_id=3)
    crud.create_game(db=db, game=game_data)

    found_game = crud.get_game_by_name(db=db, game_name="Witcher 3")
    assert found_game is not None
    assert found_game.game_name == "The Witcher 3: Wild Hunt"

    found_close_game = crud.get_game_by_name(db=db, game_name="Witcher 3: Wild Hunt")
    assert found_close_game is not None
    assert found_close_game.game_name == "The Witcher 3: Wild Hunt"

    not_found_game = crud.get_game_by_name(db=db, game_name="Totally Different Game")
    assert not_found_game is None
    db.close()

def test_get_game_by_igdb_id():
    db = TestingSessionLocal()
    game_data = schemas.GameCreate(game_name="Another Game", genre="Strategy", release_date=date(2024, 3, 10), platform="PC", igdb_id=4)
    crud.create_game(db=db, game=game_data)

    found_game = crud.get_game_by_igdb_id(db=db, igdb_id=4)
    assert found_game is not None
    assert found_game.game_name == "Another Game"

    not_found_game = crud.get_game_by_igdb_id(db=db, igdb_id=999)
    assert not_found_game is None
    db.close()

def test_create_rating():
    db = TestingSessionLocal()
    # Create a test user and game first
    user_data = schemas.UserCreateDB(username="rater", email="rate@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=20, is_admin=False)
    user = crud.create_user(db=db, user=user_data)
    game_data = schemas.GameCreate(game_name="Rated Game", genre="Indie", release_date=date(2022, 7, 15), platform="Switch", igdb_id=5)
    game = crud.create_game(db=db, game=game_data)

    rating_data = schemas.RatingCreate(user_id=user.user_id, game_id=game.game_id, rating=4.5, comment="Good game!", rating_date=datetime.utcnow())
    created_rating = crud.create_rating(db=db, rating=rating_data)
    assert created_rating is not None
    assert created_rating.user_id == user.user_id
    assert created_rating.game_id == game.game_id
    assert created_rating.rating == 4.5
    assert created_rating.comment == "Good game!"
    db.close()

def test_get_ratings():
    db = TestingSessionLocal()
    # Create some test ratings
    user1_data = schemas.UserCreateDB(username="user1_rate", email="u1@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=20, is_admin=False)
    user1 = crud.create_user(db=db, user=user1_data)
    game1_data = schemas.GameCreate(game_name="Game 1_rate", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=111)  # Use a unique igdb_id
    game1 = crud.create_game(db=db, game=game1_data)
    rating_data_1 = schemas.RatingCreate(user_id=user1.user_id, game_id=game1.game_id, rating=4.0, rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_1)

    user2_data = schemas.UserCreateDB(username="user2_rate", email="u2@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=25, is_admin=False)
    user2 = crud.create_user(db=db, user=user2_data)
    game2_data = schemas.GameCreate(game_name="Game 2_rate", genre="RPG", release_date=date(2023, 2, 1), platform="PS5", igdb_id=112)  # Use a unique igdb_id
    game2 = crud.create_game(db=db, game=game2_data)
    rating_data_2 = schemas.RatingCreate(user_id=user2.user_id, game_id=game2.game_id, rating=5.0, rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_2)

    ratings = crud.get_ratings(db=db)
    assert len(ratings) >= 2
    assert any(rating.user_id == user1.user_id and rating.game_id == game1.game_id for rating in ratings)
    assert any(rating.user_id == user2.user_id and rating.game_id == game2.game_id for rating in ratings)
    db.close()

def test_get_ratings():
    db = TestingSessionLocal()
    # Create some test ratings
    user1_data = schemas.UserCreateDB(username="user1_rate", email="u1@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=20, is_admin=False)
    user1 = crud.create_user(db=db, user=user1_data)
    game1_data = schemas.GameCreate(game_name="Game 1_rate", genre="Action", release_date=date(2023, 1, 1), platform="PC", igdb_id=11)
    game1 = crud.create_game(db=db, game=game1_data)
    rating_data_1 = schemas.RatingCreate(user_id=user1.user_id, game_id=game1.game_id, rating=4.0, rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_1)

    user2_data = schemas.UserCreateDB(username="user2_rate", email="u2@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=25, is_admin=False)
    user2 = crud.create_user(db=db, user=user2_data)
    game2_data = schemas.GameCreate(game_name="Game 2_rate", genre="RPG", release_date=date(2023, 2, 1), platform="PS5", igdb_id=12)
    game2 = crud.create_game(db=db, game=game2_data)
    rating_data_2 = schemas.RatingCreate(user_id=user2.user_id, game_id=game2.game_id, rating=5.0, rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_2)

    ratings = crud.get_ratings(db=db)
    assert len(ratings) >= 2
    assert any(rating.user_id == user1.user_id and rating.game_id == game1.game_id for rating in ratings)
    assert any(rating.user_id == user2.user_id and rating.game_id == game2.game_id for rating in ratings)
    db.close()

def test_get_ratings_by_user():
    db = TestingSessionLocal()
    user_data = schemas.UserCreateDB(username="user_ratings", email="ur@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=30, is_admin=False)
    user = crud.create_user(db=db, user=user_data)
    game1_data = schemas.GameCreate(game_name="Game A_rate", genre="Strategy", release_date=date(2024, 1, 1), platform="PC", igdb_id=13)
    game1 = crud.create_game(db=db, game=game1_data)
    rating_data_1 = schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=3.5, comment="Okay", rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_1)
    game2_data = schemas.GameCreate(game_name="Game B_rate", genre="Puzzle", release_date=date(2024, 2, 1), platform="Switch", igdb_id=14)
    game2 = crud.create_game(db=db, game=game2_data)
    rating_data_2 = schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=4.5, comment="Good!", rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_2)

    user_ratings = crud.get_ratings_by_user(db=db, user_id=user.user_id)
    assert len(user_ratings) == 2
    assert any(rating.game_id == game1.game_id and rating.rating == 3.5 for rating in user_ratings)
    assert any(rating.game_id == game2.game_id and rating.rating == 4.5 for rating in user_ratings)
    db.close()

def test_get_ratings_with_comments_by_user():
    db = TestingSessionLocal()
    user_data = schemas.UserCreateDB(username="user_comments", email="uc@example.com", password_hash="hash", registration_date=datetime.utcnow(), user_age=35, is_admin=False)
    user = crud.create_user(db=db, user=user_data)
    game1_data = schemas.GameCreate(game_name="Comment Game 1", genre="Adventure", release_date=date(2023, 5, 10), platform="PS5", igdb_id=15)
    game1 = crud.create_game(db=db, game=game1_data)
    rating_data_1 = schemas.RatingCreate(user_id=user.user_id, game_id=game1.game_id, rating=4.0, comment="Enjoyed it.", rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_1)
    game2_data = schemas.GameCreate(game_name="Comment Game 2", genre="Simulation", release_date=date(2023, 8, 1), platform="PC", igdb_id=16)
    game2 = crud.create_game(db=db, game=game2_data)
    rating_data_2 = schemas.RatingCreate(user_id=user.user_id, game_id=game2.game_id, rating=2.5, comment="Not my type.", rating_date=datetime.utcnow())
    crud.create_rating(db=db, rating=rating_data_2)

    user_ratings = crud.get_ratings_with_comments_by_user(db=db, user_id=user.user_id)
    assert len(user_ratings) == 2
    assert any(rating.game_id == game1.game_id and rating.comment == "Enjoyed it." for rating in user_ratings)
    assert any(rating.game_id == game2.game_id and rating.comment == "Not my type." for rating in user_ratings)
    db.close()
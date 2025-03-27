# app/recommendations_utils.py

import math
import requests
from collections import defaultdict
import os
import requests
from dotenv import load_dotenv

load_dotenv()

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

def get_igdb_access_token():
    """Fetches an IGDB access token."""
    url = f"https://id.twitch.tv/oauth2/token?client_id={IGDB_CLIENT_ID}&client_secret={IGDB_CLIENT_SECRET}&grant_type=client_credentials"
    response = requests.post(url)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    return response.json()["access_token"]

def get_igdb_game_data(igdb_id):
    """Fetches game data from the IGDB API."""
    access_token = get_igdb_access_token()
    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": IGDB_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    data = f'fields name, summary, genres.name, platforms.name; where id = {igdb_id};'
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def cosine_similarity(user1_ratings, user2_ratings):
    """Calculates cosine similarity between two users' ratings."""

    common_games = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_games:
        return 0  # No common ratings, no similarity

    dot_product = sum(user1_ratings[game] * user2_ratings[game] for game in common_games)
    magnitude1 = math.sqrt(sum(user1_ratings[game] ** 2 for game in common_games))
    magnitude2 = math.sqrt(sum(user2_ratings[game] ** 2 for game in common_games))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0  # Avoid division by zero

    result = dot_product / (magnitude1 * magnitude2)
    print(f"Cosine Similarity Result: {result}, type: {type(result)}") # Debugging line
    return result

def pearson_correlation(user1_ratings, user2_ratings):
    """Calculates Pearson correlation between two users' ratings."""

    common_games = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_games:
        return 0  # No common ratings, no correlation

    user1_avg = sum(user1_ratings[game] for game in common_games) / len(common_games)
    user2_avg = sum(user2_ratings[game] for game in common_games) / len(common_games)

    numerator = sum((user1_ratings[game] - user1_avg) * (user2_ratings[game] - user2_avg) for game in common_games)
    denominator1 = math.sqrt(sum((user1_ratings[game] - user1_avg) ** 2 for game in common_games))
    denominator2 = math.sqrt(sum((user2_ratings[game] - user2_avg) ** 2 for game in common_games))

    if denominator1 == 0 or denominator2 == 0:
        return 0  # Avoid division by zero

    result = numerator / (denominator1 * denominator2)
    print(f"Pearson Correlation Result: {result}, type: {type(result)}") # Debugging line
    return result

def calculate_user_similarities(user_ratings, similarity_function):
    """Calculates user-user similarities using a given function."""

    user_ids = list(user_ratings.keys())
    similarities = {}

    print(f"User IDs: {user_ids}")  # Inspect user IDs

    for i in range(len(user_ids)):
        for j in range(i + 1, len(user_ids)):
            user1_id = user_ids[i]
            user2_id = user_ids[j]

            print(f"Calculating similarity between users {user1_id} and {user2_id}")  # Inspect users
            print(f"User 1 Ratings: {user_ratings[user1_id]}")
            print(f"User 2 Ratings: {user_ratings[user2_id]}")

            similarity = similarity_function(user_ratings[user1_id], user_ratings[user2_id])

            print(f"Similarity result: {similarity}") #inspect similarity result

            similarities[f"({user1_id}, {user2_id})"] = similarity #convert tuple to string
            print(f"Similarities Dictionary: {similarities}") # Debugging line
            similarities[f"({user2_id}, {user1_id})"] = similarity  # Similarity is symmetric

    print(f"Final Similarities: {similarities}") #inspect final similarities
    return similarities

def create_item_user_matrix(ratings):
    """Creates an item-user rating matrix from ratings data."""
    print("Ratings received:")
    for rating in ratings:
        print(f"  - User: {rating.user_id}, Game: {rating.game_id}, Rating: {rating.rating}")
    matrix = defaultdict(dict)
    for rating in ratings:
        matrix[rating.game_id][rating.user_id] = rating.rating
    print("Item-User Matrix:")
    for game_id, users in matrix.items():
        print(f"  - Game: {game_id}, Users: {users}")
    return matrix

def calculate_item_similarity(item_user_matrix):
    """Calculates item-item similarities using cosine similarity."""
    print("item_user_matrix received:", item_user_matrix)
    item_ids = list(item_user_matrix.keys())
    print(f"item_ids: {item_ids}")
    similarities = {}

    for i in range(len(item_ids)):
        for j in range(i + 1, len(item_ids)):
            item1_id = item_ids[i]
            item2_id = item_ids[j]
            print(f"Comparing item {item1_id} and {item2_id}")

            item1_ratings = item_user_matrix[item1_id]
            item2_ratings = item_user_matrix[item2_id]
            print(f"item1_ratings: {item1_ratings}")
            print(f"item2_ratings: {item2_ratings}")

            if not isinstance(item1_ratings, dict) or not isinstance(item2_ratings, dict):
                print(f"Skipping similarity calculation for {item1_id} and {item2_id} due to invalid ratings data.")
                continue

            common_users = set(item1_ratings.keys()) & set(item2_ratings.keys())
            print(f"common_users: {common_users}")

            if not common_users:
                similarity = 0
            else:
                dot_product = sum(item1_ratings[user] * item2_ratings[user] for user in common_users)
                magnitude1 = math.sqrt(sum(item1_ratings[user] ** 2 for user in common_users))
                magnitude2 = math.sqrt(sum(item2_ratings[user] ** 2 for user in common_users))

                if magnitude1 == 0 or magnitude2 == 0:
                    similarity = 0
                else:
                    similarity = dot_product / (magnitude1 * magnitude2)

            similarities[f"({item1_id}, {item2_id})"] = similarity
            similarities[f"({item2_id}, {item1_id})"] = similarity #symmetric similarity.
            print(f"similarity between {item1_id} and {item2_id}: {similarity}")

    return similarities

def predict_rating(user_id, game_id, user_ratings, user_similarities):
    """Predicts the rating a user would give to a game."""

    numerator = 0
    denominator = 0
    for other_user_ids, similarity in user_similarities.items():
        u1, u2 = map(int, other_user_ids.strip('()').split(', '))
        other_user_id = u2 if u1 == user_id else u1

        if game_id in user_ratings.get(other_user_id, {}):
            numerator += similarity * user_ratings[other_user_id][game_id]
            denominator += abs(similarity)

    if denominator == 0:
        return 0  # No similar users rated the game

    return numerator / denominator
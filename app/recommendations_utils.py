# app/recommendations_utils.py

import math
import requests

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
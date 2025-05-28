# app/recommendations_utils.py

"""
Utility functions for calculating similarities and generating recommendations.

This module provides core algorithms for collaborative filtering, including
cosine similarity, Pearson correlation, user-user similarity calculation,
item-user matrix creation, item-item similarity calculation, and rating prediction.
"""

import math
from collections import defaultdict
from typing import Any, Callable, Dict, List


def cosine_similarity(user1_ratings: Dict[int, float], user2_ratings: Dict[int, float]) -> float:
    """Calculates cosine similarity between two users' ratings.

    Args:
        user1_ratings (Dict[int, float]): Dictionary of game_id to rating for user 1.
        user2_ratings (Dict[int, float]): Dictionary of game_id to rating for user 2.

    Returns:
        float: The cosine similarity score, ranging from -1 to 1. Returns 0.0 if no
               common games or if the magnitude of either user's ratings is zero.
    """
    common_games = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_games:
        return 0.0

    dot_product = sum(user1_ratings[game] * user2_ratings[game]
                      for game in common_games)
    magnitude1 = math.sqrt(sum(user1_ratings[game] ** 2
                               for game in common_games))
    magnitude2 = math.sqrt(sum(user2_ratings[game] ** 2
                               for game in common_games))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def pearson_correlation(user1_ratings: Dict[int, float], user2_ratings: Dict[int, float]) -> float:
    """Calculates Pearson correlation between two users' ratings.

    Args:
        user1_ratings (Dict[int, float]): Dictionary of game_id to rating for user 1.
        user2_ratings (Dict[int, float]): Dictionary of game_id to rating for user 2.

    Returns:
        float: The Pearson correlation coefficient, ranging from -1 to 1.
               Returns 0.0 if no common games or if denominators are zero.
    """
    common_games = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_games:
        return 0.0

    user1_avg = sum(user1_ratings[game] for game in common_games) / \
        len(common_games)
    user2_avg = sum(user2_ratings[game] for game in common_games) / \
        len(common_games)

    numerator = sum((user1_ratings[game] - user1_avg) *
                    (user2_ratings[game] - user2_avg) for game in common_games)
    denominator1 = math.sqrt(sum((user1_ratings[game] - user1_avg) ** 2
                                 for game in common_games))
    denominator2 = math.sqrt(sum((user2_ratings[game] - user2_avg) ** 2
                                 for game in common_games))

    if denominator1 == 0 or denominator2 == 0:
        return 0.0

    return numerator / (denominator1 * denominator2)


def calculate_user_similarities(
    user_ratings: Dict[int, Dict[int, float]],
    similarity_function: Callable[[Dict[int, float], Dict[int, float]], float]
) -> Dict[str, float]:
    """Calculates user-user similarities using a given function.

    Args:
        user_ratings (Dict[int, Dict[int, float]]): A dictionary where keys are
                                                     user_ids and values are
                                                     dictionaries of game_id to rating.
        similarity_function (Callable): The function to use for calculating
                                        similarity (e.g., cosine_similarity,
                                        pearson_correlation).

    Returns:
        Dict[str, float]: A dictionary of similarities where keys are
                          string representations of user ID pairs (e.g., "(1, 2)")
                          and values are their similarity scores.
    """
    user_ids = list(user_ratings.keys())
    similarities = {}

    for i, user1_id in enumerate(user_ids):
        for user2_id in user_ids[i + 1:]:
            similarity = similarity_function(user_ratings[user1_id],
                                             user_ratings[user2_id])

            similarities[f"({user1_id}, {user2_id})"] = similarity
            similarities[f"({user2_id}, {user1_id})"] = similarity

    return similarities


def create_item_user_matrix(ratings: List[Any]) -> Dict[int, Dict[int, float]]:
    """Creates an item-user rating matrix from ratings data.

    Args:
        ratings (List[Any]): A list of rating objects (e.g., from your models.Rating),
                             each with `user_id`, `game_id`, and `rating` attributes.

    Returns:
        Dict[int, Dict[int, float]]: A dictionary where keys are game_ids and
                                     values are dictionaries of user_id to rating.
    """
    matrix = defaultdict(dict)
    for rating in ratings:
        matrix[rating.game_id][rating.user_id] = rating.rating
    return matrix


def calculate_item_similarity(item_user_matrix: Dict[int, Dict[int, float]]) -> Dict[str, float]:
    """Calculates item-item similarities using cosine similarity.

    Args:
        item_user_matrix (Dict[int, Dict[int, float]]): An item-user rating matrix
                                                         (game_id -> user_id -> rating).

    Returns:
        Dict[str, float]: A dictionary of similarities where keys are
                          string representations of item ID pairs (e.g., "(1, 2)")
                          and values are their similarity scores.
    """
    item_ids = list(item_user_matrix.keys())
    similarities = {}

    for i, item1_id in enumerate(item_ids):
        for item2_id in item_ids[i + 1:]:
            item1_ratings = item_user_matrix[item1_id]
            item2_ratings = item_user_matrix[item2_id]

            # Ensure ratings are dictionary types before proceeding
            if not isinstance(item1_ratings, dict) or \
               not isinstance(item2_ratings, dict):
                continue

            common_users = set(item1_ratings.keys()) & set(item2_ratings.keys())

            if not common_users:
                similarity = 0.0
            else:
                dot_product = sum(item1_ratings[user] * item2_ratings[user]
                                  for user in common_users)
                magnitude1 = math.sqrt(sum(item1_ratings[user] ** 2
                                           for user in common_users))
                magnitude2 = math.sqrt(sum(item2_ratings[user] ** 2
                                           for user in common_users))

                if magnitude1 == 0 or magnitude2 == 0:
                    similarity = 0.0
                else:
                    similarity = dot_product / (magnitude1 * magnitude2)

            similarities[f"({item1_id}, {item2_id})"] = similarity
            similarities[f"({item2_id}, {item1_id})"] = similarity

    return similarities


def predict_rating(
    user_id: int,
    game_id: int,
    user_ratings: Dict[int, Dict[int, float]],
    user_similarities: Dict[str, float]
) -> float:
    """Predicts the rating a user would give to a game using user-based collaborative filtering.

    Args:
        user_id (int): The ID of the user for whom to predict the rating.
        game_id (int): The ID of the game for which to predict the rating.
        user_ratings (Dict[int, Dict[int, float]]): A dictionary where keys are user_ids
                                                     and values are dictionaries of
                                                     game_id to rating.
        user_similarities (Dict[str, float]): A dictionary of similarities where keys are
                                              string representations of user ID pairs
                                              (e.g., "(1, 2)") and values are their
                                              similarity scores.

    Returns:
        float: The predicted rating for the user-game pair. Returns 0.0 if no similar
               users rated the game.
    """
    numerator = 0.0
    denominator = 0.0

    for user_pair_str, similarity in user_similarities.items():
        # Strip parentheses and split by comma-space to get user IDs
        u1, u2 = map(int, user_pair_str.strip('()').split(', '))

        other_user_id = u2 if u1 == user_id else u1
        if other_user_id == user_id:
            continue

        if game_id in user_ratings.get(other_user_id, {}):
            numerator += similarity * user_ratings[other_user_id][game_id]
            denominator += abs(similarity)

    if denominator == 0:
        return 0.0

    return numerator / denominator
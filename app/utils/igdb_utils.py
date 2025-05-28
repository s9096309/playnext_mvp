# app/utils/igdb_utils.py

"""
Utility functions for interacting with the IGDB API.

This module handles authentication with IGDB and provides methods to
search for games, retrieve game details by ID, and fetch cover image URLs.
It also includes a mapping for IGDB age ratings to a simplified format.
"""

import os
import json
from igdb.wrapper import IGDBWrapper
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "IGDB_CLIENT_ID or IGDB_CLIENT_SECRET not found in environment variables."
        " Please ensure your .env file or deployment environment sets these."
    )

wrapper = IGDBWrapper(CLIENT_ID, CLIENT_SECRET)

def search_games_igdb(query: str) -> list[dict] | None:
    """
    Searches for games on IGDB by query string.

    Args:
        query (str): The search query for the game title.

    Returns:
        list[dict] | None: A list of dictionaries representing game data from IGDB,
                           or None if an error occurs.
    """
    try:
        byte_array = wrapper.api_request(
            "games",
            (f'search "{query}"; fields name, cover.url, genres.name, '
             'platforms.name, id, age_ratings.rating, release_dates.human; limit 10;')
        )
        result = json.loads(byte_array)
        return result
    except Exception as e:
        print(f"Error searching IGDB: {e}")
        return None

def get_game_by_id_igdb(game_id: int) -> list[dict] | None:
    """
    Retrieves game details from IGDB by its unique IGDB ID.

    Args:
        game_id (int): The unique ID of the game on IGDB.

    Returns:
        list[dict] | None: A list of dictionaries representing game data from IGDB,
                           or None if an error occurs.
    """
    try:
        byte_array = wrapper.api_request(
            "games",
            (f'fields name, cover.url, genres.name, platforms.name, id, '
             f'age_ratings.rating, release_dates.human; where id = {game_id};')
        )
        result = json.loads(byte_array)
        return result
    except Exception as e:
        print(f"Error getting game from IGDB: {e}")
        return None

def get_cover_url(cover_id: int) -> str | None:
    """
    Retrieves the cover URL for a game from the IGDB API.

    Args:
        cover_id (int): The ID of the cover image.

    Returns:
        str | None: The URL of the cover, or None if an error occurs or URL not found.
    """
    try:
        byte_array = wrapper.api_request(
            "covers",
            f'fields url; where id = ({cover_id});'
        )

        if byte_array is None:
            return None

        result = json.loads(byte_array)

        if result and len(result) > 0 and 'url' in result[0]:
            url = result[0]['url'].replace('t_thumb', 't_cover_big')
            if not url.startswith("https:"):
                url = "https:" + url
            return url
        else:
            return None
    except Exception as e:
        print(f"Error getting cover url from IGDB: {e}")
        return None

IGDB_AGE_RATING_MAP: dict[int, str] = {
    1: "3",
    2: "7",
    3: "12",
    4: "16",
    5: "18",
    6: "RP",
    7: "EC",
    8: "E",
    9: "E10+",
    10: "T",
    11: "M",
    12: "AO",
    13: "CUSA",
    14: "PEGI 3",
    15: "PEGI 7",
    16: "PEGI 12",
    17: "PEGI 16",
    18: "PEGI 18",
    19: "ACB E",
    20: "ACB PG",
    21: "ACB M",
    22: "ACB MA15+",
    23: "ACB AV15+",
    24: "ACB R18+",
    25: "ACB RC",
}

def map_igdb_age_rating(igdb_rating: int) -> str | None:
    """
    Maps an IGDB age rating ID to a more human-readable string.

    Args:
        igdb_rating (int): The integer ID of the age rating from IGDB.

    Returns:
        str | None: The mapped age rating string (e.g., "E10+", "PEGI 18"),
                    or None if the ID is not found in the map.
    """
    return IGDB_AGE_RATING_MAP.get(igdb_rating)


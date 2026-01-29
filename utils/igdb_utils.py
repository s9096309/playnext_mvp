# app/utils/igdb_utils.py

"""
Utility functions for interacting with the IGDB API.

This module handles authentication with IGDB and provides methods to
search for games, retrieve game details by ID, and fetch cover image URLs.
It also includes a mapping for IGDB age ratings to a simplified format.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv

# Configure logging for this module
logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)
# Basic console handler
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Load environment variables
load_dotenv()

# Retrieve API credentials from environment variables
CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")
CURRENT_IGDB_ACCESS_TOKEN: Optional[str] = os.getenv("IGDB_APP_ACCESS_TOKEN")

# Validate that necessary environment variables are loaded
if not CLIENT_ID or not CLIENT_SECRET:
    logger.critical(
        "IGDB_CLIENT_ID or IGDB_CLIENT_SECRET not found in environment variables. "
        "Please ensure your .env file or deployment environment sets these."
    )
    # Raising an error here will stop the application early if credentials are missing
    raise ValueError(
        "Missing IGDB API credentials. Please set IGDB_CLIENT_ID and IGDB_CLIENT_SECRET."
    )

# Base URL for IGDB API
IGDB_API_BASE_URL = "https://api.igdb.com/v4/"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def get_new_igdb_app_access_token() -> Optional[str]:
    """
    Obtains a new Twitch App Access Token using Client ID and Client Secret.
    This token is required for authenticating with the IGDB API.

    Returns:
        Optional[str]: The new access token if successful, None otherwise.
    """
    global CURRENT_IGDB_ACCESS_TOKEN
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        logger.info("Attempting to get new Twitch App Access Token...")
        response = httpx.post(TWITCH_TOKEN_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        new_token = token_data.get("access_token")
        if new_token:
            CURRENT_IGDB_ACCESS_TOKEN = new_token
            logger.info("Successfully acquired new Twitch App Access Token.")
            logger.debug("New token: %s", new_token) # Log token for debugging
            return new_token
        else:
            logger.error("New access token not found in Twitch response: %s", token_data)
            return None
    except httpx.HTTPStatusError as e:
        logger.error(
            "Failed to get Twitch token - HTTP Error: %s - %s",
            e.response.status_code, e.response.text
        )
        return None
    except httpx.RequestError as e:
        logger.error("Failed to get Twitch token - Request Error: %s", e)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred during token acquisition: %s", e)
        return None


# Initial check/refresh for the token when the module loads
if not CURRENT_IGDB_ACCESS_TOKEN:
    logger.warning("IGDB_APP_ACCESS_TOKEN not found in .env, attempting to acquire a new one.")
    get_new_igdb_app_access_token()
    if not CURRENT_IGDB_ACCESS_TOKEN: # If acquisition failed at startup
        logger.critical(
            "Failed to acquire IGDB_APP_ACCESS_TOKEN during startup. "
            "IGDB API calls will likely fail."
        )
elif "YOUR_MANUALLY_GENERATED_TOKEN" in CURRENT_IGDB_ACCESS_TOKEN: # Placeholder check
    logger.info("Detected placeholder token, attempting to acquire a new Twitch App Access Token.")
    get_new_igdb_app_access_token()
else:
    logger.info("IGDB_APP_ACCESS_TOKEN found in .env. Using existing token.")


def _make_igdb_request(endpoint: str, body: str) -> Optional[bytes]:
    """
    Helper to make direct HTTP POST requests to IGDB API.
    Handles token refreshing if a 401 Unauthorized error occurs.

    Args:
        endpoint (str): The IGDB API endpoint (e.g., "games", "covers").
        body (str): The IGDB API query string.

    Returns:
        Optional[bytes]: The raw byte response from IGDB, or None if an error occurs.
    """
    if not CURRENT_IGDB_ACCESS_TOKEN:
        logger.error("No IGDB access token available. Cannot make API request to %s.", endpoint)
        return None

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {CURRENT_IGDB_ACCESS_TOKEN}"
    }
    url = f"{IGDB_API_BASE_URL}{endpoint}"

    try:
        logger.debug("Making request to %s with body: %s", url, body)
        response = httpx.post(url, headers=headers, content=body, timeout=10.0)
        response.raise_for_status()  # Raises an exception for 4xx/5xx responses
        logger.debug("Successful response from %s (Status: %d).", endpoint, response.status_code)
        return response.content
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error making IGDB request to %s: %s - %s",
            endpoint, e.response.status_code, e.response.text
        )
        # If it's a 401 Unauthorized, try to refresh token and retry
        if e.response.status_code == 401:
            logger.warning("IGDB token unauthorized, attempting to refresh token and retry request...")
            if get_new_igdb_app_access_token():
                # Update headers with the new token for retry
                headers["Authorization"] = f"Bearer {CURRENT_IGDB_ACCESS_TOKEN}"
                try:
                    logger.info("Retrying request after token refresh...")
                    response = httpx.post(url, headers=headers, content=body, timeout=10.0)
                    response.raise_for_status()
                    logger.debug("Successful retry response from %s (Status: %d).", endpoint, response.status_code)
                    return response.content
                except httpx.RequestError as retry_e:
                    logger.error("Retry failed after token refresh: %s", retry_e)
                except httpx.HTTPStatusError as retry_e:
                    logger.error(
                        "Retry failed with HTTP error after token refresh: %s - %s",
                        retry_e.response.status_code, retry_e.response.text
                    )
            else:
                logger.error("Failed to refresh token, cannot retry IGDB request.")
        return None
    except httpx.RequestError as e:
        logger.error("Request error making IGDB request to %s: %s", endpoint, e)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred during IGDB request to %s: %s", endpoint, e)
        return None


def search_games_igdb(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Searches for games on IGDB by query string using direct httpx.

    Args:
        query (str): The search query for the game title.

    Returns:
        Optional[List[dict]]: A list of dictionaries representing game data from IGDB,
                              or None if an error occurs.
    """

    body = (f'search "{query}"; fields name, url, genres.name, '
            'platforms.name, id, cover.url; limit 5;')

    byte_array = _make_igdb_request("games", body)
    if byte_array:
        try:
            result = json.loads(byte_array)
            logger.debug("IGDB search result for '%s': %s", query, result)
            return result
        except json.JSONDecodeError as e:
            logger.error("JSON decode error for search '%s': %s. Raw response: %s", query, e, byte_array)
            return None
    logger.debug("No byte array received from IGDB for search '%s'.", query)
    return None


def get_game_by_id_igdb(game_id: int) -> Optional[List[Dict[str, Any]]]: # Changed return type hint
    """
    Retrieves game details from IGDB by its unique IGDB ID using direct httpx.

    Args:
        game_id (int): The unique ID of the game on IGDB.

    Returns:
        Optional[List[dict]]: A list of dictionaries representing game data from IGDB,
                              or None if an error occurs.
    """
    body = (f'fields name, url, genres.name, platforms.name, id, '
            f'age_ratings.rating, release_dates.human, cover.url; where id = {game_id};')

    byte_array = _make_igdb_request("games", body)
    if byte_array:
        try:
            result = json.loads(byte_array)
            logger.debug("IGDB get by ID result for %s: %s", game_id, result) # Debug line
            return result
        except json.JSONDecodeError as e:
            logger.error("JSON decode error for game ID %s: %s. Raw response: %s", game_id, e, byte_array) # Added raw response
            return None
    logger.debug("No byte array received from IGDB for game ID %s.", game_id) # Debug line
    return None


def get_cover_url(cover_id: int) -> Optional[str]:
    """
    Retrieves the cover URL for a game from the IGDB API using direct httpx.
    Note: It's often more efficient to get the cover URL directly from the game search result
    if 'cover.url' field is requested there, rather than a separate call.

    Args:
        cover_id (int): The ID of the cover image.

    Returns:
        Optional[str]: The URL of the cover, or None if an error occurs or URL not found.
    """
    body = f'fields url; where id = ({cover_id});'

    byte_array = _make_igdb_request("covers", body)
    if byte_array:
        try:
            result = json.loads(byte_array)
            if result and len(result) > 0 and 'url' in result[0]:
                url = result[0]['url'].replace('t_thumb', 't_cover_big') # Ensure large cover
                if not url.startswith("https:"):
                    url = "https:" + url
                logger.debug("Cover URL for ID %s: %s", cover_id, url) # Debug line
                return url
            else:
                logger.info("No URL found for cover ID %s in response: %s", cover_id, result)
                return None
        except json.JSONDecodeError as e:
            logger.error("JSON decode error for cover ID %s: %s. Raw response: %s", cover_id, e, byte_array) # Added raw response
            return None
    logger.debug("No byte array received from IGDB for cover ID %s.", cover_id) # Debug line
    return None


# Mapping from IGDB age rating IDs to human-readable strings.
# You can expand this mapping if needed
IGDB_AGE_RATING_MAP: Dict[int, str] = {
    1: "3", 2: "7", 3: "12", 4: "16", 5: "18", 6: "RP", 7: "EC", 8: "E", 9: "E10+",
    10: "T", 11: "M", 12: "AO", 13: "CUSA", 14: "PEGI 3", 15: "PEGI 7", 16: "PEGI 12",
    17: "PEGI 16", 18: "PEGI 18", 19: "ACB E", 20: "ACB PG", 21: "ACB M", 22: "ACB MA15+",
    23: "ACB AV15+", 24: "ACB R18+", 25: "ACB RC",
}


def map_igdb_age_rating(igdb_rating: int) -> Optional[str]:
    """
    Maps an IGDB age rating ID to a more human-readable string.

    Args:
        igdb_rating (int): The integer ID of the age rating from IGDB.

    Returns:
        Optional[str]: The mapped age rating string (e.g., "E10+", "PEGI 18"),
                       or None if the ID is not found in the map.
    """
    return IGDB_AGE_RATING_MAP.get(igdb_rating)
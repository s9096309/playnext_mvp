import os
from igdb.wrapper import IGDBWrapper
import json

CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
APP_ACCESS_TOKEN = os.getenv("IGDB_APP_ACCESS_TOKEN")

print(f"IGDB_CLIENT_ID: {CLIENT_ID}")
print(f"IGDB_APP_ACCESS_TOKEN: {APP_ACCESS_TOKEN}")

if not CLIENT_ID or not APP_ACCESS_TOKEN:
    raise ValueError("IGDB_CLIENT_ID or IGDB_APP_ACCESS_TOKEN not found in environment variables.")

wrapper = IGDBWrapper(CLIENT_ID, APP_ACCESS_TOKEN)

def search_games_igdb(query):
    try:
        byte_array = wrapper.api_request(
            "games",
            f'search "{query}"; fields name, cover.url, genres.name, platforms.name, id, age_ratings.rating, release_dates.human; limit 10;' # added release_dates.human
        )
        import json
        result = json.loads(byte_array)
        print("IGDB API Response:", result) # Add this line for debugging
        return result
    except Exception as e:
        print(f"Error searching IGDB: {e}")
        return None

def get_game_by_id_igdb(game_id):
    try:
        byte_array = wrapper.api_request(
            "games",
            f'fields name, cover.url, genres.name, platforms.name, id, age_ratings.rating, release_dates.human; where id = {game_id};'
        )
        import json
        result = json.loads(byte_array)
        print("IGDB API Response (get_game_by_id): ", result)
        return result
    except Exception as e:
        print(f"Error getting game from IGDB: {e}")
        return None



def get_cover_url(cover_id):
    """
    Retrieves the cover URL for a game from the IGDB API.

    Args:
        cover_id (int): The ID of the cover.

    Returns:
        str: The URL of the cover, or None if an error occurs.
    """
    print(f"DEBUG: get_cover_url called with cover_id: {cover_id}")  # Debug: Print the input

    try:
        byte_array = wrapper.api_request(
            "covers",
            f'fields url; where id = ({cover_id});' # Only the integer id here.
        )
        print(f"DEBUG: IGDB API response byte_array: {byte_array}")  # Debug: Print the raw response

        if byte_array is None: #check if the byte_array is none.
            print(f"DEBUG: IGDB API request returned None for cover_id: {cover_id}")
            return None

        result = json.loads(byte_array)
        print(f"DEBUG: IGDB API response JSON: {result}")  # Debug: Print the parsed JSON

        if result and len(result) > 0 and 'url' in result[0]:
            url = result[0]['url'].replace('t_thumb', 't_cover_big')
            url = "https:" + url
            print(f"DEBUG: Returning cover URL: {url}")  # Debug: Print the final URL
            return url
        else:
            print(f"Error: Could not find url in IGDB response: {result}")
            return None
    except Exception as e:
        print(f"Error getting cover url from IGDB: {e}")
        return None
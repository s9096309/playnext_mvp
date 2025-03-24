import os
from igdb.wrapper import IGDBWrapper

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
    try:
        byte_array = wrapper.api_request(
            "covers",
            f'fields url; where id = {cover_id};'
        )
        import json
        result = json.loads(byte_array)
        return result
    except Exception as e:
        print(f"Error getting cover url from IGDB: {e}")
        return None
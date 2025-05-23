import os
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable is not set or accessible.")
    print("Please set it before running this script (e.g., export DATABASE_URL='...')")
    exit(1)

print(f"Attempting to connect to: {DATABASE_URL}")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar() # Simple test query
        if result == 1:
            print("Successfully connected to the database!")
        else:
            print("Connection successful, but simple test query failed.")
    engine.dispose() # Close the engine connection pool
except OperationalError as e:
    print(f"Failed to connect to the database (OperationalError): {e}")
    print("Common causes: Database not running, incorrect host/port, wrong username/password, firewall.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
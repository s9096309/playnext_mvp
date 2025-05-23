import os
import sys

# Add your project root to sys.path so 'app.database.models' can be found
# This path should point to the directory containing your 'app' folder
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import your Base object. This import is crucial for registering your models.
    # Make sure this path exactly matches where your Base and models are defined.
    # Assumes your models are in 'app/database/models.py'
    from app.database.models import Base

    # It's also good practice to explicitly import your model classes here
    # to ensure they are parsed and registered with Base.metadata.
    # Uncommenting these lines helps ensure all model definitions are processed.
    # from app.database.models import User
    # from app.database.models import Game
    # from app.database.models import BacklogItem
    # from app.database.models import Recommendation
    # from app.database.models import Rating
    # from app.database.models import BacklogStatus
    # from app.database.models import Genre
    # from app.database.models import Platform
    # from app.database.models import UserGameRating # If this is a separate model

    print(f"--- Checking Base.metadata.tables ---")
    if not Base.metadata.tables:
        print("WARNING: Base.metadata.tables is EMPTY. Alembic will not detect any models.")
        print("This means your SQLAlchemy models are either not imported correctly or not defined.")
    else:
        print("SUCCESS: Base.metadata.tables contains the following tables:")
        for table_name, table_obj in Base.metadata.tables.items():
            print(f"- {table_name}: {len(table_obj.columns)} columns")
        print("\nModels appear to be loaded into Base.metadata.")

except ImportError as e:
    print(f"ERROR: Could not import your models: {e}")
    print("Please check the 'from app.database.models import Base' line in this script and your env.py.")
    print("Ensure 'app' is in your PYTHONPATH or that sys.path is correctly configured.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
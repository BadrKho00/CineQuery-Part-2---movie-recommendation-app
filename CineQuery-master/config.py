import os

# --- App ---
PAGE_TITLE = "CineQuery"
PAGE_ICON = "🎬"
LAYOUT = "wide"

# --- BigQuery ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "mscis-488614")
BQ_DATASET = os.environ.get("BQ_DATASET", "movielens")
BQ_MOVIES_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.movies"
BQ_RATINGS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.ratings"

# --- External API (TMDB) ---
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "80dd03e7af0225d28da79ba60f81e842")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# --- Search defaults ---
DEFAULT_MIN_RATING = 0.0
DEFAULT_MAX_RESULTS = 50

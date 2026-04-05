import os

# ── Google Cloud / BigQuery ──────────────────────────────────────────────────
GCP_PROJECT_ID   = os.environ.get("GCP_PROJECT_ID",  "mscis-488614")
BQ_DATASET       = os.environ.get("BQ_DATASET",       "movielens")
BQ_MOVIES_TABLE  = f"{GCP_PROJECT_ID}.{BQ_DATASET}.ml-small-movies"
BQ_RATINGS_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.ml-small-ratings"
BQ_LINKS_TABLE   = f"{GCP_PROJECT_ID}.{BQ_DATASET}.ml-small-links"
BQ_MODEL         = f"{GCP_PROJECT_ID}.{BQ_DATASET}.recommender"

# ── Elasticsearch ────────────────────────────────────────────────────────────
ES_URL     = os.environ.get("ES_URL")
ES_API_KEY = os.environ.get("ES_API_KEY")
ES_INDEX   = "movies"

# ── TMDB ─────────────────────────────────────────────────────────────────────
TMDB_API_KEY    = os.environ.get("TMDB_API_KEY")
TMDB_BASE_URL   = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# ── Recommendation tuning ────────────────────────────────────────────────────
HIGH_RATING_THRESHOLD  = 0.7   # rating_im threshold to consider a movie "liked"
TOP_SIMILAR_USERS      = 5     # how many similar users to pull recommendations from
TOP_N_RECOMMENDATIONS  = 20    # movies to return
GLOBAL_MIN_RATINGS     = 30    # minimum number of ratings for global top list

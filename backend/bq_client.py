from google.cloud import bigquery
from config import (
    GCP_PROJECT_ID, BQ_MOVIES_TABLE, BQ_RATINGS_TABLE,
    BQ_LINKS_TABLE, BQ_MODEL,
    HIGH_RATING_THRESHOLD, TOP_SIMILAR_USERS, TOP_N_RECOMMENDATIONS,
    GLOBAL_MIN_RATINGS,
)
from title_utils import fix_title

_client = None


def get_client() -> bigquery.Client:
    global _client
    if _client is None:
        _client = bigquery.Client(project=GCP_PROJECT_ID)
    return _client


def _run(sql: str) -> list[dict]:
    print("\n" + "=" * 60)
    print("EXECUTING SQL:")
    print(sql)
    print("=" * 60)
    rows = get_client().query(sql).result()
    results = [dict(r) for r in rows]
    print(f"RESULT: {len(results)} rows\n")
    return results


def get_all_movies() -> list[dict]:
    """Fetch all movies joined with links (for Elasticsearch indexing)."""
    sql = f"""
SELECT
  m.movieId,
  m.title,
  m.genres,
  l.tmdbId
FROM `{BQ_MOVIES_TABLE}` m
LEFT JOIN `{BQ_LINKS_TABLE}` l ON m.movieId = l.movieId
"""
    return _run(sql)


def find_similar_users(movie_ids: list[int]) -> list[dict]:
    """
    Find users who rated the selected movies highly (>= HIGH_RATING_THRESHOLD).
    Ranks by number of common preferred movies, returns top TOP_SIMILAR_USERS.
    """
    if not movie_ids:
        return []

    ids_str = ", ".join(str(m) for m in movie_ids)
    sql = f"""
SELECT
  CAST(userId AS INT64) AS userId,
  COUNT(*)              AS common_movies
FROM `{BQ_RATINGS_TABLE}`
WHERE movieId  IN ({ids_str})
  AND rating_im >= {HIGH_RATING_THRESHOLD}
GROUP BY userId
ORDER BY common_movies DESC
LIMIT {TOP_SIMILAR_USERS}
"""
    return _run(sql)


def get_ml_recommendations(user_ids: list[int], exclude_movie_ids: list[int]) -> list[dict]:
    """
    Use BigQuery ML RECOMMEND to get predictions for the similar users,
    then aggregate by movie and exclude already-selected films.
    """
    if not user_ids:
        return []

    users_str = ", ".join(str(u) for u in user_ids)

    exclude_clause = ""
    if exclude_movie_ids:
        exclude_str = ", ".join(str(m) for m in exclude_movie_ids)
        exclude_clause = f"AND r.movieId NOT IN ({exclude_str})"

    sql = f"""
WITH recs AS (
  SELECT
    predicted_rating_im,
    userId,
    movieId
  FROM ML.RECOMMEND(
    MODEL `{BQ_MODEL}`,
    (SELECT userId FROM UNNEST([{users_str}]) AS userId)
  )
)
SELECT
  r.movieId,
  m.title,
  m.genres,
  l.tmdbId,
  ROUND(AVG(r.predicted_rating_im), 4)  AS avg_predicted_rating,
  COUNT(DISTINCT r.userId)               AS num_users_recommending
FROM recs r
JOIN `{BQ_MOVIES_TABLE}` m ON r.movieId = m.movieId
LEFT JOIN `{BQ_LINKS_TABLE}` l        ON r.movieId = l.movieId
WHERE r.predicted_rating_im IS NOT NULL
  {exclude_clause}
GROUP BY r.movieId, m.title, m.genres, l.tmdbId
ORDER BY num_users_recommending DESC, avg_predicted_rating DESC
LIMIT {TOP_N_RECOMMENDATIONS}
"""
    rows = _run(sql)
    for r in rows:
        r["title"] = fix_title(r["title"])
    return rows


def get_global_recommendations() -> list[dict]:
    """
    Fallback when no movies are selected: top-rated movies with enough ratings.
    """
    sql = f"""
SELECT
  m.movieId,
  m.title,
  m.genres,
  l.tmdbId,
  ROUND(AVG(r.rating_im), 4) AS avg_rating,
  COUNT(r.userId)             AS rating_count
FROM `{BQ_MOVIES_TABLE}` m
JOIN `{BQ_RATINGS_TABLE}` r  ON m.movieId = r.movieId
LEFT JOIN `{BQ_LINKS_TABLE}` l ON m.movieId = l.movieId
GROUP BY m.movieId, m.title, m.genres, l.tmdbId
HAVING COUNT(r.userId) >= {GLOBAL_MIN_RATINGS}
ORDER BY avg_rating DESC, rating_count DESC
LIMIT {TOP_N_RECOMMENDATIONS}
"""
    rows = _run(sql)
    for r in rows:
        r["title"] = fix_title(r["title"])
    return rows

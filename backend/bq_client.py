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
    Hybrid recommendations:
    - ML.RECOMMEND predictions for similar users
    - Boosted by movies the similar users actually rated highly
    - Penalised by global popularity to avoid always showing blockbusters
    """
    if not user_ids:
        return []

    users_str = ", ".join(str(u) for u in user_ids)

    exclude_clause = ""
    if exclude_movie_ids:
        exclude_str = ", ".join(str(m) for m in exclude_movie_ids)
        exclude_clause = f"AND r.movieId NOT IN ({exclude_str})"

    sql = f"""
WITH ml_recs AS (
  -- BigQuery ML predicted ratings for similar users
  SELECT predicted_rating_im, userId, movieId
  FROM ML.RECOMMEND(
    MODEL `{BQ_MODEL}`,
    (SELECT userId FROM UNNEST([{users_str}]) AS userId)
  )
),
actual_likes AS (
  -- Movies the similar users actually rated highly in the dataset
  SELECT movieId, COUNT(*) AS liked_by_similar
  FROM `{BQ_RATINGS_TABLE}`
  WHERE CAST(userId AS INT64) IN ({users_str})
    AND rating_im >= {HIGH_RATING_THRESHOLD}
  GROUP BY movieId
),
global_popularity AS (
  -- How many users rated each movie overall (popularity penalty)
  SELECT movieId, COUNT(*) AS total_ratings
  FROM `{BQ_RATINGS_TABLE}`
  GROUP BY movieId
),
aggregated AS (
  SELECT
    r.movieId,
    AVG(r.predicted_rating_im)                        AS avg_predicted,
    COUNT(DISTINCT r.userId)                           AS num_users_recommending,
    COALESCE(MAX(al.liked_by_similar), 0)              AS actual_likes_count,
    COALESCE(MAX(gp.total_ratings), 1)                 AS total_ratings
  FROM ml_recs r
  LEFT JOIN actual_likes  al ON r.movieId = al.movieId
  LEFT JOIN global_popularity gp ON r.movieId = gp.movieId
  WHERE r.predicted_rating_im IS NOT NULL
    {exclude_clause}
  GROUP BY r.movieId
)
SELECT
  a.movieId,
  m.title,
  m.genres,
  l.tmdbId,
  ROUND(a.avg_predicted, 4) AS avg_predicted_rating,
  a.num_users_recommending,
  -- Hybrid score: ML prediction + actual like boost - log popularity penalty
  ROUND(
    a.avg_predicted
    + (a.actual_likes_count * 0.05)
    - (LOG(a.total_ratings) * 0.02),
  4) AS hybrid_score
FROM aggregated a
JOIN `{BQ_MOVIES_TABLE}` m ON a.movieId = m.movieId
LEFT JOIN `{BQ_LINKS_TABLE}` l ON a.movieId = l.movieId
ORDER BY hybrid_score DESC
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

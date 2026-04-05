from google.cloud import bigquery
from db.client import get_bq_client
from config import BQ_MOVIES_TABLE, BQ_RATINGS_TABLE, DEFAULT_MAX_RESULTS
import streamlit as st


def build_search_query(filters: dict) -> tuple[str, dict]:
    """
    Build a parameterised BigQuery SQL query from the user filters.
    Returns (sql_string, query_params_dict).
    """
    title_query = filters.get("title", "").strip()
    language = filters.get("language", "")
    genre = filters.get("genre", "")
    min_year = filters.get("min_year")
    max_year = filters.get("max_year")
    min_rating = filters.get("min_rating", 0.0)
    limit = filters.get("limit", DEFAULT_MAX_RESULTS)

    use_rating_join = min_rating and min_rating > 0.0

    # ── SELECT / FROM ────────────────────────────────────────────────────────
    if use_rating_join:
        select_block = f"""
SELECT
    m.movieId,
    m.title,
    m.genres,
    m.language,
    m.release_year,
    m.country,
    m.tmdbId,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.rating)         AS rating_count
FROM `{BQ_MOVIES_TABLE}` m
JOIN `{BQ_RATINGS_TABLE}` r ON m.movieId = r.movieId"""
    else:
        select_block = f"""
SELECT
    m.movieId,
    m.title,
    m.genres,
    m.language,
    m.release_year,
    m.country,
    m.tmdbId,
    NULL  AS avg_rating,
    NULL  AS rating_count
FROM `{BQ_MOVIES_TABLE}` m"""

    # ── WHERE ─────────────────────────────────────────────────────────────────
    conditions = []
    params = []

    if title_query:
        conditions.append("LOWER(m.title) LIKE LOWER(@title_pattern)")
        params.append(
            bigquery.ScalarQueryParameter("title_pattern", "STRING", f"%{title_query}%")
        )

    if language:
        conditions.append("m.language = @language")
        params.append(bigquery.ScalarQueryParameter("language", "STRING", language))

    if genre:
        conditions.append("m.genres LIKE @genre_pattern")
        params.append(
            bigquery.ScalarQueryParameter("genre_pattern", "STRING", f"%{genre}%")
        )

    if min_year:
        conditions.append("m.release_year >= @min_year")
        params.append(bigquery.ScalarQueryParameter("min_year", "INT64", int(min_year)))

    if max_year:
        conditions.append("m.release_year <= @max_year")
        params.append(bigquery.ScalarQueryParameter("max_year", "INT64", int(max_year)))

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + "\n  AND ".join(conditions)

    # ── GROUP BY / HAVING ────────────────────────────────────────────────────
    group_having = ""
    if use_rating_join:
        group_having = """GROUP BY
    m.movieId, m.title, m.genres, m.language,
    m.release_year, m.country, m.tmdbId"""
        if min_rating:
            group_having += f"\nHAVING AVG(r.rating) >= @min_rating"
            params.append(
                bigquery.ScalarQueryParameter("min_rating", "FLOAT64", float(min_rating))
            )

    # ── ORDER / LIMIT ─────────────────────────────────────────────────────────
    order_limit = f"ORDER BY m.title ASC\nLIMIT {int(limit)}"

    sql = "\n".join(
        part for part in [select_block, where_clause, group_having, order_limit] if part.strip()
    )
    return sql, params


def run_query(sql: str, params: list) -> list[dict]:
    """Execute a BigQuery query and return rows as list of dicts."""
    client = get_bq_client()
    job_config = bigquery.QueryJobConfig(query_parameters=params)

    print("\n" + "=" * 70)
    print("EXECUTING SQL:")
    print(sql)
    if params:
        print("\nPARAMETERS:")
        for p in params:
            print(f"  @{p.name} = {p.value!r}")
    print("=" * 70 + "\n")

    query_job = client.query(sql, job_config=job_config)
    rows = query_job.result()
    results = [dict(row) for row in rows]
    print(f"RESULT: {len(results)} rows returned\n")
    return results


def search_movies(filters: dict) -> tuple[list[dict], str]:
    """Public entry point: build query, run it, return (rows, sql)."""
    sql, params = build_search_query(filters)
    rows = run_query(sql, params)
    return rows, sql


def get_autocomplete_suggestions(prefix: str, limit: int = 10) -> list[str]:
    """Return up to `limit` title suggestions matching the prefix."""
    if not prefix or len(prefix) < 2:
        return []
    sql = f"""
SELECT DISTINCT title
FROM `{BQ_MOVIES_TABLE}`
WHERE LOWER(title) LIKE LOWER(@prefix)
ORDER BY title ASC
LIMIT {int(limit)}
"""
    params = [bigquery.ScalarQueryParameter("prefix", "STRING", f"{prefix}%")]
    client = get_bq_client()
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    print(f"\n[AUTOCOMPLETE SQL]\n{sql}\n  @prefix = {prefix!r}\n")
    rows = client.query(sql, job_config=job_config).result()
    return [row["title"] for row in rows]


def get_distinct_languages() -> list[str]:
    sql = f"SELECT DISTINCT language FROM `{BQ_MOVIES_TABLE}` WHERE language IS NOT NULL ORDER BY language"
    print(f"\n[LANGUAGES SQL]\n{sql}\n")
    client = get_bq_client()
    rows = client.query(sql).result()
    return [r["language"] for r in rows]


def get_distinct_genres() -> list[str]:
    """Extract individual genres from the pipe-separated genres column."""
    sql = f"""
SELECT DISTINCT genre
FROM `{BQ_MOVIES_TABLE}`,
UNNEST(SPLIT(genres, '|')) AS genre
WHERE genre IS NOT NULL AND genre != ''
ORDER BY genre
"""
    print(f"\n[GENRES SQL]\n{sql}\n")
    client = get_bq_client()
    rows = client.query(sql).result()
    return [r["genre"] for r in rows]

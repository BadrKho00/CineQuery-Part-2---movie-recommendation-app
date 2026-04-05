import requests
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE


def get_poster_url(tmdb_id) -> str | None:
    """Return a full poster URL for a TMDB movie ID, or None on failure."""
    if not tmdb_id:
        return None
    try:
        resp = requests.get(
            f"{TMDB_BASE_URL}/movie/{int(tmdb_id)}",
            params={"api_key": TMDB_API_KEY},
            timeout=5,
        )
        if resp.status_code == 200:
            path = resp.json().get("poster_path")
            if path:
                return f"{TMDB_IMAGE_BASE}{path}"
    except Exception as exc:
        print(f"[TMDB] Error for tmdbId={tmdb_id}: {exc}")
    return None


def enrich_with_posters(movies: list[dict]) -> list[dict]:
    """Add a 'poster_url' key to each movie dict in-place."""
    for m in movies:
        m["poster_url"] = get_poster_url(m.get("tmdbId"))
    return movies

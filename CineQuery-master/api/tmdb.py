import requests
import streamlit as st
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE


@st.cache_data(ttl=3600)
def fetch_tmdb_details(tmdb_id: int) -> dict | None:
    """Fetch movie details (poster, overview, cast, etc.) from TMDB."""
    if not TMDB_API_KEY or not tmdb_id:
        return None
    try:
        # Main details
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        r = requests.get(url, params={"api_key": TMDB_API_KEY, "append_to_response": "credits"}, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()

        poster_path = data.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        cast = []
        if "credits" in data:
            cast = [
                {"name": m["name"], "character": m.get("character", ""), "profile": f"{TMDB_IMAGE_BASE}{m['profile_path']}" if m.get("profile_path") else None}
                for m in data["credits"].get("cast", [])[:6]
            ]

        return {
            "poster_url": poster_url,
            "overview": data.get("overview", ""),
            "tagline": data.get("tagline", ""),
            "runtime": data.get("runtime"),
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "budget": data.get("budget"),
            "revenue": data.get("revenue"),
            "cast": cast,
            "homepage": data.get("homepage", ""),
            "tmdb_url": f"https://www.themoviedb.org/movie/{tmdb_id}",
        }
    except Exception as e:
        print(f"[TMDB ERROR] {e}")
        return None

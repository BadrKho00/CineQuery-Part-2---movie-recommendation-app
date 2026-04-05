import streamlit as st
from api.tmdb import fetch_tmdb_details


def render_results(results: list[dict]):
    """Display movie results as a grid of cards."""
    if not results:
        st.info("No movies found. Try adjusting your filters.")
        return

    count = len(results)
    st.markdown(f'<div class="results-header">{count} movie{"s" if count != 1 else ""} found</div>',
                unsafe_allow_html=True)

    cols_per_row = 4
    for row_start in range(0, len(results), cols_per_row):
        row_movies = results[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, movie in zip(cols, row_movies):
            with col:
                _render_card(movie)


def _render_card(movie: dict):
    """Render a single movie card."""
    tmdb_id = movie.get("tmdbId")
    tmdb = fetch_tmdb_details(int(tmdb_id)) if tmdb_id else None

    poster = tmdb["poster_url"] if tmdb and tmdb.get("poster_url") else "https://via.placeholder.com/200x300?text=No+Poster"
    title = movie.get("title", "Unknown")
    year = movie.get("release_year", "")
    genres = movie.get("genres", "").replace("|", " · ")

    avg_rating_raw = movie.get("avg_rating")
    try:
        avg_rating_val = round(float(avg_rating_raw), 2) if avg_rating_raw is not None else None
    except (TypeError, ValueError):
        avg_rating_val = None

    title_safe = title.replace("<", "").replace(">", "")
    genres_safe = genres[:40].replace("<", "").replace(">", "")
    lang_safe = movie.get('language', '').upper().replace("<", "").replace(">", "")

    st.image(poster, use_column_width=True)
    st.markdown(f"**{title_safe}**")
    st.caption(f"{year} · {lang_safe} · {genres_safe}")
    if avg_rating_val:
        st.caption(f"⭐ {avg_rating_val}")

    if st.button("Details", key=f"btn_{movie['movieId']}", use_container_width=True):
        st.session_state.selected_movie = {**movie, "_tmdb": tmdb}
        st.rerun()
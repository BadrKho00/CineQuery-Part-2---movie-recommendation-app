"""
CineQuery – Streamlit Frontend
Talks to the Flask backend via BACKEND_URL env variable.
"""

import os
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080").rstrip("/")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineQuery",
    page_icon="🎬",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Header */
  .cq-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 28px;
  }
  .cq-header h1 { color: #fff; margin: 0; font-size: 2.4rem; }
  .cq-header p  { color: #aaa; margin: 4px 0 0; font-size: 1rem; }

  /* Search area */
  .stTextInput > div > div > input {
    font-size: 1.05rem;
    border-radius: 8px;
  }

  /* Suggestion buttons */
  .suggestion-btn button {
    background: #1e1e2e !important;
    color: #e0e0e0 !important;
    border: 1px solid #444 !important;
    border-radius: 8px !important;
    text-align: left !important;
    width: 100% !important;
    margin-bottom: 4px;
  }
  .suggestion-btn button:hover { background: #2a2a3e !important; }

  /* Selected movie chips */
  .chip {
    display: inline-block;
    background: #302b63;
    color: #fff;
    border-radius: 20px;
    padding: 4px 14px;
    margin: 4px;
    font-size: 0.85rem;
  }

  /* Movie cards */
  .movie-card {
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    height: 100%;
  }
  .movie-title {
    color: #1a1a2e;
    font-weight: 600;
    font-size: 0.82rem;
    margin-top: 8px;
    line-height: 1.3;
  }
  .movie-genres {
    color: #555;
    font-size: 0.72rem;
    margin-top: 4px;
  }

  /* Section headers */
  .section-title {
    color: #1a1a2e;
    font-size: 1.25rem;
    font-weight: 700;
    margin: 24px 0 12px;
    border-left: 4px solid #7c6ff7;
    padding-left: 10px;
  }

  /* Recommendation badge */
  .rec-badge {
    background: #7c6ff7;
    color: #fff;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    display: inline-block;
    margin-bottom: 16px;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cq-header">
  <h1>🎬 CineQuery</h1>
  <p>Personalised movie recommendations powered by BigQuery ML &amp; Elasticsearch</p>
</div>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "selected_movies" not in st.session_state:
    st.session_state.selected_movies = []   # [{movieId, title, genres}]
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""


# ── Helper ────────────────────────────────────────────────────────────────────
def _is_selected(movie_id: int) -> bool:
    return any(m["movieId"] == movie_id for m in st.session_state.selected_movies)


def _call_backend(path: str, **kwargs):
    try:
        return requests.request(kwargs.pop("method", "GET"), f"{BACKEND_URL}{path}", **kwargs)
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot reach backend at {BACKEND_URL}. Is the Flask server running?")
        return None


# ═══════════════════════════════════════════════════════════════════
# SECTION 1 – Search & autocomplete
# ═══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Search for movies you like</div>', unsafe_allow_html=True)
st.caption("Type at least 2 characters — results come from Elasticsearch in real time.")

search_query = st.text_input(
    label="Movie search",
    placeholder="e.g. Toy Story, The Matrix, Inception …",
    label_visibility="collapsed",
    key="search_input",
)

if search_query and len(search_query.strip()) >= 2:
    resp = _call_backend("/autocomplete", params={"q": search_query.strip()})
    suggestions = resp.json() if resp and resp.status_code == 200 else []

    if suggestions:
        st.caption(f"{len(suggestions)} suggestions from Elasticsearch:")
        cols = st.columns(2)
        for idx, movie in enumerate(suggestions):
            already = _is_selected(movie["movieId"])
            label   = f"{'✓' if already else '+'} {movie['title']}"
            col     = cols[idx % 2]
            with col:
                st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
                if st.button(label, key=f"sug_{movie['movieId']}", disabled=already):
                    st.session_state.selected_movies.append(movie)
                    st.session_state.recommendations = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No suggestions found. Try a different title.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 2 – Selected movies
# ═══════════════════════════════════════════════════════════════════
if st.session_state.selected_movies:
    st.markdown('<div class="section-title">Your selected movies</div>', unsafe_allow_html=True)

    chips_html = "".join(
        f'<span class="chip">🎬 {m["title"]}</span>'
        for m in st.session_state.selected_movies
    )
    st.markdown(chips_html, unsafe_allow_html=True)

    # Remove buttons (one per movie)
    remove_cols = st.columns(min(len(st.session_state.selected_movies), 5))
    for i, movie in enumerate(st.session_state.selected_movies):
        with remove_cols[i % 5]:
            if st.button(f"✕ Remove", key=f"rm_{movie['movieId']}"):
                st.session_state.selected_movies = [
                    m for m in st.session_state.selected_movies
                    if m["movieId"] != movie["movieId"]
                ]
                st.session_state.recommendations = None
                st.rerun()

    st.markdown("")  # spacing


# ═══════════════════════════════════════════════════════════════════
# SECTION 3 – Get recommendations button
# ═══════════════════════════════════════════════════════════════════
btn_label = (
    "Get Personalised Recommendations"
    if st.session_state.selected_movies
    else "Show Global Top Movies"
)

if st.button(btn_label, type="primary", use_container_width=True):
    movie_ids = [m["movieId"] for m in st.session_state.selected_movies]
    with st.spinner("Fetching recommendations…"):
        resp = _call_backend("/recommend", method="POST", json={"movie_ids": movie_ids})
    if resp and resp.status_code == 200:
        st.session_state.recommendations = resp.json()
    else:
        st.error("Backend error. Check the Flask logs.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 4 – Display recommendations
# ═══════════════════════════════════════════════════════════════════
if st.session_state.recommendations:
    data  = st.session_state.recommendations
    recs  = data.get("recommendations", [])
    rtype = data.get("type", "")

    # Header / badge
    if rtype == "global":
        st.markdown('<div class="section-title">Global Top-Rated Movies</div>', unsafe_allow_html=True)
        st.markdown('<span class="rec-badge">No selection — showing all-time favourites</span>', unsafe_allow_html=True)

    elif rtype == "global_fallback":
        st.markdown('<div class="section-title">Global Top-Rated Movies</div>', unsafe_allow_html=True)
        st.markdown(
            '<span class="rec-badge">No similar users found for your selection — showing global favourites</span>',
            unsafe_allow_html=True,
        )

    else:  # personalized
        similar = data.get("similar_users", [])
        st.markdown('<div class="section-title">Personalised Recommendations</div>', unsafe_allow_html=True)

        # Show similarity explanation
        user_lines = "  \n".join(
            f"User **{u['userId']}** — {u['common_movies']} movie(s) in common"
            for u in similar
        )
        with st.expander(f"How we found your recommendations ({len(similar)} similar users)"):
            st.markdown(
                "We identified users in the dataset who rated the same movies highly "
                f"(rating ≥ {0.7}). We ranked them by the number of shared preferred movies "
                "and used BigQuery ML matrix factorisation to generate their predicted ratings.\n\n"
                + user_lines
            )

    # ── Movie grid ───────────────────────────────────────────────────────────
    COLS = 5
    for row_start in range(0, len(recs), COLS):
        row_movies = recs[row_start: row_start + COLS]
        cols       = st.columns(COLS)
        for col, movie in zip(cols, row_movies):
            with col:
                genres_display = movie.get("genres", "").replace("|", " · ")
                poster = movie.get("poster_url")
                if poster:
                    st.image(poster, use_column_width=True)
                else:
                    st.markdown(
                        '<div style="height:200px;background:#2a2a3e;border-radius:8px;'
                        'display:flex;align-items:center;justify-content:center;'
                        'font-size:3rem;">🎬</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="movie-title">{movie["title"]}</div>'
                    f'<div class="movie-genres">{genres_display}</div>',
                    unsafe_allow_html=True,
                )

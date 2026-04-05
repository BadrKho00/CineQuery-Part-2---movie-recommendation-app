import streamlit as st
from db.queries import get_distinct_languages, get_distinct_genres
from datetime import datetime

CURRENT_YEAR = datetime.now().year


@st.cache_data(ttl=600)
def _load_languages():
    return [""] + get_distinct_languages()


@st.cache_data(ttl=600)
def _load_genres():
    return [""] + get_distinct_genres()


def render_sidebar() -> dict:
    """Render the left sidebar with all filters. Returns filter dict."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🔍 Search Filters</div>', unsafe_allow_html=True)

        title_input = st.text_input("Movie title", placeholder="e.g. Inception", key="title_input")

        st.markdown("---")
        st.markdown("**Advanced Filters**")

        try:
            languages = _load_languages()
            language = st.selectbox("Language", languages, key="lang_select",
                                    format_func=lambda x: x if x else "Any language")
        except Exception:
            language = ""
            st.caption("⚠️ Could not load languages")

        try:
            genres = _load_genres()
            genre = st.selectbox("Genre", genres, key="genre_select",
                                 format_func=lambda x: x if x else "Any genre")
        except Exception:
            genre = ""
            st.caption("⚠️ Could not load genres")

        st.markdown("**Release Year Range**")
        col1, col2 = st.columns(2)
        with col1:
            min_year = st.number_input("From", min_value=1888, max_value=CURRENT_YEAR,
                                       value=1888, step=1, key="min_year")
        with col2:
            max_year = st.number_input("To", min_value=1888, max_value=CURRENT_YEAR,
                                       value=CURRENT_YEAR, step=1, key="max_year")

        min_rating = st.slider(
            "Min. average rating ⭐", min_value=0.0, max_value=5.0,
            value=0.0, step=0.1, key="min_rating",
            help="Only show movies with average user rating above this value"
        )

        limit = st.select_slider(
            "Max results", options=[10, 25, 50, 100, 200], value=50, key="limit"
        )

        st.markdown("---")
        search_clicked = st.button("🔎  Search", use_container_width=True, type="primary")

        # Show last SQL in expander
        if "last_sql" in st.session_state:
            with st.expander("Last SQL query"):
                st.code(st.session_state.last_sql, language="sql")

    return {
        "title": title_input,
        "language": language,
        "genre": genre,
        "min_year": min_year if min_year > 1888 else None,
        "max_year": max_year if max_year < CURRENT_YEAR else None,
        "min_rating": min_rating if min_rating > 0 else None,
        "limit": limit,
        "search_clicked": search_clicked,
    }

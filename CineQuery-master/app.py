import streamlit as st
from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from ui.sidebar import render_sidebar
from ui.results import render_results
from ui.movie_detail import render_movie_detail

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)

# Inject custom CSS
with open("ui/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="header-bar">
    <span class="header-icon">🎬</span>
    <span class="header-title">CineQuery</span>
    <span class="header-sub">MovieLens × BigQuery</span>
</div>
""", unsafe_allow_html=True)

# Session state init
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "results" not in st.session_state:
    st.session_state.results = None

# Sidebar returns filters + trigger
filters = render_sidebar()

if filters.get("search_clicked"):
    from db.queries import search_movies
    results, sql = search_movies(filters)
    st.session_state.results = results
    st.session_state.last_sql = sql
    st.session_state.selected_movie = None

if st.session_state.results is not None:
    if st.session_state.selected_movie is not None:
        render_movie_detail(st.session_state.selected_movie)
    else:
        render_results(st.session_state.results)
else:
    st.markdown("""
    <div class="hero">
        <div class="hero-text">Search millions of movies.<br>Filter by genre, language, year & rating.</div>
    </div>
    """, unsafe_allow_html=True)

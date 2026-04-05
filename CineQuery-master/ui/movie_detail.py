import streamlit as st


def render_movie_detail(movie: dict):
    """Full-page detail view for a selected movie."""
    tmdb = movie.get("_tmdb") or {}

    if st.button("← Back to results"):
        st.session_state.selected_movie = None
        st.rerun()

    st.markdown("---")
    col_poster, col_info = st.columns([1, 2.5])

    with col_poster:
        poster = tmdb.get("poster_url") or "https://via.placeholder.com/300x450?text=No+Poster"
        st.image(poster, use_column_width=True)

        if tmdb.get("tmdb_url"):
            st.markdown(f"[View on TMDB ↗]({tmdb['tmdb_url']})")

    with col_info:
        title = movie.get("title", "")
        year = movie.get("release_year", "")
        st.markdown(f"<h1 class='detail-title'>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='detail-tagline'>{tmdb.get('tagline','')}</p>", unsafe_allow_html=True)

        # Metadata pills
        pills = []
        if year:
            pills.append(str(year))
        if movie.get("language"):
            pills.append(movie["language"].upper())
        if tmdb.get("runtime"):
            pills.append(f"{tmdb['runtime']} min")
        pill_html = " ".join(f'<span class="pill">{p}</span>' for p in pills)
        st.markdown(pill_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Genres
        genres = movie.get("genres", "").split("|")
        genre_html = " ".join(f'<span class="genre-pill">{g}</span>' for g in genres if g)
        st.markdown(genre_html, unsafe_allow_html=True)

        # Ratings
        avg_rating = movie.get("avg_rating")
        tmdb_vote = tmdb.get("vote_average")
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            if avg_rating:
                st.metric("MovieLens Rating", f"⭐ {avg_rating}/5", f"{movie.get('rating_count', 0)} ratings")
        with r_col2:
            if tmdb_vote:
                st.metric("TMDB Rating", f"🎬 {tmdb_vote}/10", f"{tmdb.get('vote_count', 0)} votes")

        # Overview
        if tmdb.get("overview"):
            st.markdown("**Overview**")
            st.markdown(tmdb["overview"])

        # Country
        if movie.get("country"):
            st.markdown(f"🌍 **Country:** {movie['country']}")

    # Cast
    cast = tmdb.get("cast", [])
    if cast:
        st.markdown("---")
        st.markdown("### Cast")
        cast_cols = st.columns(len(cast))
        for col, member in zip(cast_cols, cast):
            with col:
                if member.get("profile"):
                    st.image(member["profile"], use_column_width=True)
                else:
                    st.markdown("👤")
                st.markdown(f"**{member['name']}**")
                st.caption(member.get("character", ""))

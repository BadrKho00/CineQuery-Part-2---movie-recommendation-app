"""
CineQuery – Flask Backend
Endpoints:
  GET  /health                  – liveness probe
  GET  /autocomplete?q=<prefix> – Elasticsearch title suggestions
  POST /index-movies             – (re-)index all BQ movies into ES (run once)
  POST /recommend               – body: {"movie_ids": [...]}
                                  returns personalised or global recommendations
"""

from flask import Flask, request, jsonify

from es_client   import autocomplete, index_movies
from bq_client   import (
    get_all_movies,
    find_similar_users,
    get_ml_recommendations,
    get_global_recommendations,
)
from tmdb_client import enrich_with_posters

app = Flask(__name__)


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ── Autocomplete ──────────────────────────────────────────────────────────────

@app.route("/autocomplete")
def autocomplete_route():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    results = autocomplete(q)
    print(f"[AUTOCOMPLETE] q={q!r} → {len(results)} suggestions")
    return jsonify(results)


# ── Index movies into Elasticsearch ───────────────────────────────────────────

@app.route("/index-movies", methods=["POST"])
def index_movies_route():
    """Fetch all movies from BigQuery and index them into Elasticsearch."""
    movies = get_all_movies()
    count  = index_movies(movies)
    return jsonify({"status": "indexed", "count": count})


# ── Recommendations ───────────────────────────────────────────────────────────

@app.route("/recommend", methods=["POST"])
def recommend():
    data      = request.get_json(force=True, silent=True) or {}
    movie_ids = [int(m) for m in data.get("movie_ids", [])]

    # ── No movies selected → global top-rated list ────────────────────────
    if not movie_ids:
        print("[RECOMMEND] No movies selected → global recommendations")
        movies = get_global_recommendations()
        enrich_with_posters(movies)
        return jsonify({"type": "global", "recommendations": movies})

    # ── Find similar users ────────────────────────────────────────────────
    similar_users = find_similar_users(movie_ids)
    print(f"[RECOMMEND] Similar users: {similar_users}")

    if not similar_users:
        print("[RECOMMEND] No similar users found → global fallback")
        movies = get_global_recommendations()
        enrich_with_posters(movies)
        return jsonify({"type": "global_fallback", "recommendations": movies})

    # ── BigQuery ML recommendations ───────────────────────────────────────
    user_ids = [u["userId"] for u in similar_users]
    movies   = get_ml_recommendations(user_ids, exclude_movie_ids=movie_ids)
    enrich_with_posters(movies)

    return jsonify({
        "type":         "personalized",
        "similar_users": similar_users,
        "recommendations": movies,
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

# CineQuery — Personalised Movie Recommendations

**Live URL:** https://cinequery-frontend-183604469593.us-central1.run.app

A two-tier movie recommendation application built on Google Cloud, powered by BigQuery ML matrix factorisation and Elasticsearch autocomplete.

---

## Architecture

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Streamlit | Cloud Run |
| Backend | Flask (REST API) | Cloud Run |
| Search / Autocomplete | Elasticsearch (Elastic Cloud) | Elastic Cloud (GCP Belgium) |
| Recommendation Model | BigQuery ML — Matrix Factorisation | BigQuery |
| Movie Metadata | BigQuery (MovieLens ml-small) | BigQuery |
| Posters | TMDB API | External |

---

## Features

- **Elasticsearch autocomplete** — movie title suggestions appear as you type, powered by a full-text index of 9,742 movies
- **Multi-movie selection** — select one or more movies you like
- **Personalised recommendations** — BigQuery ML predicts ratings for similar users and returns the top 20 movies
- **Global fallback** — if no movies are selected, or no similar users are found, the app shows the top-rated movies from the dataset
- **Movie posters** — fetched from the TMDB API for each recommendation
- **SQL query logging** — all BigQuery queries are printed to the backend terminal on every request

---

## Similarity Computation

The application solves the **cold-start problem** using user-based collaborative filtering:

1. The web app user selects movies they like (no user ID exists for them in the training data).
2. We query `ml-small-ratings` for all dataset users who rated those same movies with a score ≥ 0.7 (on a 0–1 normalised scale).
3. Users are ranked by the **number of movies in common** with the web app user — the more shared preferred movies, the more similar the user.
4. The **top 5 most similar users** are passed to `ML.RECOMMEND()` on the trained BigQuery ML matrix factorisation model.
5. Their predicted ratings are aggregated: movies are ranked first by how many similar users were recommended them, then by average predicted rating.
6. Movies the user already selected are excluded from the results.

**Example:** if the user selects *Toy Story* and *The Matrix*, we find dataset users who rated both highly, rank them by overlap count, and use BigQuery ML to generate predictions for those users — surfacing movies the cold-start user is likely to enjoy.

---

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Flask + Gunicorn
- **Search:** Elasticsearch 8 (Elastic Cloud Serverless)
- **Database:** Google BigQuery (MovieLens ml-small dataset)
- **ML Model:** BigQuery ML — Matrix Factorisation (explicit feedback, 16 factors)
- **Deployment:** Google Cloud Run (two separate containers)
- **Containerisation:** Docker
- **Poster API:** TMDB (The Movie Database)

---

## Local Development

### Prerequisites
- Docker Desktop
- A `gcp-key.json` service account key placed in the project root

### Run locally

```bash
docker compose up --build
```

Then index movies into Elasticsearch (run once):

```bash
curl -X POST http://localhost:8080/index-movies
```

Open the app at `http://localhost:8501`.

---

## Deployment

Both services are deployed on Google Cloud Run in `us-central1`.

### Backend
```bash
gcloud builds submit ./backend --tag us-central1-docker.pkg.dev/mscis-488614/cinequery/backend
gcloud run deploy cinequery-backend \
  --image us-central1-docker.pkg.dev/mscis-488614/cinequery/backend \
  --platform managed --region us-central1 --allow-unauthenticated \
  --memory 512Mi --env-vars-file backend.env.yaml
```

### Frontend
```bash
gcloud builds submit ./frontend --tag us-central1-docker.pkg.dev/mscis-488614/cinequery/frontend
gcloud run deploy cinequery-frontend \
  --image us-central1-docker.pkg.dev/mscis-488614/cinequery/frontend \
  --platform managed --region us-central1 --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars BACKEND_URL=https://cinequery-backend-183604469593.us-central1.run.app
```

After deploying the backend, index movies into Elasticsearch:

```bash
curl -X POST https://cinequery-backend-183604469593.us-central1.run.app/index-movies
```

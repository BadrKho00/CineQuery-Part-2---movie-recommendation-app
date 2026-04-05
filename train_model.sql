-- ============================================================
-- Step 1: Train the Matrix Factorization recommendation model
-- Run this once in the BigQuery console.
-- Expected training time: ~5-10 minutes on ml-small dataset.
-- ============================================================
CREATE OR REPLACE MODEL `mscis-488614.movielens.recommender`
OPTIONS (
  model_type      = 'matrix_factorization',
  user_col        = 'userId',
  item_col        = 'movieId',
  rating_col      = 'rating_im',
  feedback_type   = 'explicit',
  num_factors     = 16
) AS
SELECT
  CAST(userId  AS INT64) AS userId,
  CAST(movieId AS INT64) AS movieId,
  rating_im
FROM `mscis-488614.movielens.ml-small-ratings`;


-- ============================================================
-- Step 2: Verify the model was created
-- ============================================================
SELECT *
FROM ML.TRAINING_INFO(MODEL `mscis-488614.movielens.recommender`);


-- ============================================================
-- Step 3: Smoke-test — generate recommendations for user 1
-- ============================================================
SELECT *
FROM ML.RECOMMEND(
  MODEL `mscis-488614.movielens.recommender`,
  (SELECT 1 AS userId)
)
ORDER BY predicted_rating_im DESC
LIMIT 10;

-- NOTE: If the column is named predicted_rating_im_confidence instead of
-- predicted_rating_im, update bq_client.py line that references it.

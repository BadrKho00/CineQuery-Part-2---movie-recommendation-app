from google.cloud import bigquery
import streamlit as st

@st.cache_resource
def get_bq_client():
    """Return a cached BigQuery client."""
    return bigquery.Client()

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from config import ES_URL, ES_API_KEY, ES_INDEX
from title_utils import fix_title

_client = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(ES_URL, api_key=ES_API_KEY)
    return _client


def _create_index_if_missing(es: Elasticsearch) -> None:
    if es.indices.exists(index=ES_INDEX):
        return
    es.indices.create(
        index=ES_INDEX,
        body={
            "settings": {"analysis": {"analyzer": {"default": {"type": "standard"}}}},
            "mappings": {
                "properties": {
                    "movieId":       {"type": "integer"},
                    "title":         {"type": "text", "analyzer": "standard",
                                      "fields": {"keyword": {"type": "keyword"}}},
                    "title_display": {"type": "keyword"},
                    "genres":        {"type": "keyword"},
                    "tmdbId":        {"type": "integer"},
                }
            },
        },
    )
    print(f"[ES] Created index '{ES_INDEX}'")


def index_movies(movies: list[dict]) -> int:
    """
    Bulk-index movies into Elasticsearch.
    Each movie dict must have: movieId, title, genres, tmdbId (nullable).
    Returns the number of documents indexed.
    """
    es = get_es_client()
    _create_index_if_missing(es)

    actions = [
        {
            "_index": ES_INDEX,
            "_id":    m["movieId"],
            "_source": {
                "movieId":       m["movieId"],
                "title":         m["title"],          # raw (for matching)
                "title_display": fix_title(m["title"]),  # human-readable
                "genres":        m.get("genres", ""),
                "tmdbId":        m.get("tmdbId"),
            },
        }
        for m in movies
    ]

    success, _ = bulk(es, actions)
    print(f"[ES] Indexed {success} movies into '{ES_INDEX}'")
    return success


def autocomplete(prefix: str, limit: int = 10) -> list[dict]:
    """
    Return up to `limit` movie suggestions whose title starts with `prefix`.
    Uses match_phrase_prefix so "toy" matches "Toy Story".
    """
    es = get_es_client()
    resp = es.search(
        index=ES_INDEX,
        body={
            "query": {
                "match_phrase_prefix": {
                    "title": {"query": prefix, "max_expansions": 50}
                }
            },
            "_source": ["movieId", "title_display", "genres"],
            "size": limit,
        },
    )
    return [
        {
            "movieId": hit["_source"]["movieId"],
            "title":   hit["_source"]["title_display"],
            "genres":  hit["_source"].get("genres", ""),
        }
        for hit in resp["hits"]["hits"]
    ]

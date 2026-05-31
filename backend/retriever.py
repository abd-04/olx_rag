import logging
import os
import time
from threading import Lock

import chromadb
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

LOGGER = logging.getLogger(__name__)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)
CHROMA_PATH = os.getenv(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "scraper", "chroma_data"),
)
MAX_VECTOR_DISTANCE = float(os.getenv("MAX_VECTOR_DISTANCE", "0.85"))
RRF_K = 60
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "olxdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}
DATABASE_URL = os.getenv("DATABASE_URL")
FILTER_FIELDS = {
    "city", "max_price", "min_price", "brand", "model", "year",
    "transmission", "fuel", "max_km", "vehicle_type", "engine_cc",
}
MODEL_LOCK = Lock()
CHROMA_LOCK = Lock()
_embedding_model = None
_chroma_client = None
_chroma_collection = None


class RetrievalUnavailable(RuntimeError):
    pass


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with MODEL_LOCK:
            if _embedding_model is None:
                LOGGER.info("Loading embedding model %s", EMBEDDING_MODEL)
                _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_chroma_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        with CHROMA_LOCK:
            if _chroma_collection is None:
                try:
                    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
                    _chroma_collection = _chroma_client.get_collection("olx_listings")
                except Exception as error:
                    raise RetrievalUnavailable(
                        "The listing index is not ready. Run the ingestion job first."
                    ) from error
    return _chroma_collection


def normalize_filters(filters):
    return {
        key: value
        for key, value in (filters or {}).items()
        if key in FILTER_FIELDS and value not in (None, "")
    }


def numeric_sql(column):
    return f"NULLIF(regexp_replace(coalesce({column}, ''), '[^0-9]', '', 'g'), '')::BIGINT"


def build_filter_clause(filters):
    clauses = []
    params = []

    def ilike(column, key):
        if filters.get(key):
            clauses.append(f"{column} ILIKE %s")
            params.append(f"%{filters[key]}%")

    ilike("city", "city")
    ilike("transmission", "transmission")
    ilike("fuel", "fuel")
    ilike("vehicle_type", "vehicle_type")
    ilike("engine_cc", "engine_cc")

    if filters.get("max_price"):
        clauses.append("price_pkr <= %s")
        params.append(filters["max_price"])
    if filters.get("min_price"):
        clauses.append("price_pkr >= %s")
        params.append(filters["min_price"])
    if filters.get("year"):
        clauses.append("year = %s")
        params.append(str(filters["year"]))
    if filters.get("max_km"):
        clauses.append(f"{numeric_sql('km_driven')} <= %s")
        params.append(filters["max_km"])
    for key in ("brand", "model"):
        if filters.get(key):
            clauses.append("title ILIKE %s")
            params.append(f"%{filters[key]}%")

    return (" AND " + " AND ".join(clauses)) if clauses else "", params


def query_postgres(question, filters, candidate_limit=1000):
    clause, params = build_filter_clause(filters)
    lexical_query = """
        SELECT id,
               ts_rank(
                   to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, '')),
                   plainto_tsquery('simple', %s)
               ) AS lexical_score
        FROM listings
        WHERE 1=1 {clause}
        ORDER BY lexical_score DESC, id DESC
        LIMIT %s
    """.format(clause=clause)

    try:
        with get_postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(lexical_query, [question, *params, candidate_limit])
                rows = cursor.fetchall()
    except Exception as error:
        LOGGER.exception("PostgreSQL retrieval failed")
        raise RetrievalUnavailable("PostgreSQL retrieval is unavailable.") from error

    candidate_ids = [str(row[0]) for row in rows]
    lexical_ids = [str(row[0]) for row in rows if row[1] and row[1] > 0]
    return candidate_ids, lexical_ids


def query_chroma(question, candidate_ids, top_k):
    if candidate_ids == []:
        return [], {}

    vector = get_embedding_model().encode(question).tolist()
    try:
        query_args = dict(
            query_embeddings=[vector],
            n_results=max(top_k, 1),
            include=["distances"],
        )
        if candidate_ids is not None:
            query_args["ids"] = candidate_ids
            query_args["n_results"] = min(top_k, len(candidate_ids))
        result = get_chroma_collection().query(**query_args)
    except RetrievalUnavailable:
        raise
    except Exception as error:
        LOGGER.exception("Chroma retrieval failed")
        raise RetrievalUnavailable("Semantic retrieval is unavailable.") from error

    ids = result["ids"][0]
    distances = result.get("distances", [[]])[0]
    accepted = [
        listing_id
        for listing_id, distance in zip(ids, distances)
        if distance is None or distance <= MAX_VECTOR_DISTANCE
    ]
    return accepted, dict(zip(ids, distances))


def reciprocal_rank_fusion(rankings, limit):
    scores = {}
    for ranking in rankings:
        for rank, listing_id in enumerate(ranking, start=1):
            scores[listing_id] = scores.get(listing_id, 0) + 1 / (RRF_K + rank)
    return [
        listing_id
        for listing_id, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ][:limit]


def fetch_listings_by_ids(ids, distances):
    if not ids:
        return []

    int_ids = [int(listing_id) for listing_id in ids]
    try:
        with get_postgres_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, price_pkr, price_lakh, city, year,
                           km_driven, fuel, transmission, vehicle_type,
                           engine_cc, description, url
                    FROM listings
                    WHERE id = ANY(%s)
                    ORDER BY array_position(%s, id)
                """, (int_ids, int_ids))
                rows = cursor.fetchall()
    except Exception as error:
        LOGGER.exception("Listing detail fetch failed")
        raise RetrievalUnavailable("Listing details are unavailable.") from error

    return [{
        "id": row[0],
        "title": row[1],
        "price_pkr": row[2],
        "price_lakh": row[3],
        "city": row[4],
        "year": row[5],
        "km_driven": row[6],
        "fuel": row[7],
        "transmission": row[8],
        "vehicle_type": row[9],
        "engine_cc": row[10],
        "description": row[11],
        "url": row[12],
        "vector_distance": distances.get(str(row[0])),
    } for row in rows]


def get_postgres_connection():
    return psycopg2.connect(DATABASE_URL) if DATABASE_URL else psycopg2.connect(**DB_CONFIG)


def retrieve(question, filters, top_k=5):
    started = time.perf_counter()
    filters = normalize_filters(filters)
    candidate_ids, lexical_ids = query_postgres(question, filters)

    # A strict filter miss is a real miss. Never fall back to unrelated listings.
    if filters and not candidate_ids:
        LOGGER.info("No candidates matched strict filters=%s", filters)
        return []

    semantic_scope = candidate_ids if filters else None
    semantic_ids, distances = query_chroma(question, semantic_scope, top_k * 4)
    fused_ids = reciprocal_rank_fusion([semantic_ids, lexical_ids], top_k)
    listings = fetch_listings_by_ids(fused_ids, distances)

    unique_listings = []
    seen_urls = set()
    for listing in listings:
        if listing["url"] not in seen_urls:
            unique_listings.append(listing)
            seen_urls.add(listing["url"])

    LOGGER.info(
        "retrieval filters=%s candidates=%s lexical=%s semantic=%s selected_ids=%s latency_ms=%.1f",
        filters,
        len(candidate_ids),
        len(lexical_ids),
        len(semantic_ids),
        [listing["id"] for listing in unique_listings],
        (time.perf_counter() - started) * 1000,
    )
    return unique_listings

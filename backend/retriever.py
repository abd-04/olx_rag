import os
import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ─────────────────────────────
# CONNECTIONS + MODEL
# ─────────────────────────────

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DB", "olxdb"),
    "user":     os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "pakistan")
}

CHROMA_PATH = os.environ.get(
    "CHROMA_PATH",
    os.path.join(os.path.dirname(__file__), "..", "scraper", "chroma_data")
)

print("Loading embedding model...")
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Embedding model ready")

chroma_client     = chromadb.PersistentClient(path=CHROMA_PATH)
chroma_collection = chroma_client.get_collection("olx_listings")


# ─────────────────────────────
# STEP 1 — POSTGRESQL QUERY
# ─────────────────────────────

def query_postgres(filters: dict) -> list:
    query  = "SELECT id FROM listings WHERE 1=1"
    params = []

    if filters.get("city"):
        query += " AND city ILIKE %s"
        params.append(f"%{filters['city']}%")

    if filters.get("max_price"):
        query += " AND price_pkr <= %s"
        params.append(filters["max_price"])

    if filters.get("min_price"):
        query += " AND price_pkr >= %s"
        params.append(filters["min_price"])

    if filters.get("transmission"):
        query += " AND transmission ILIKE %s"
        params.append(f"%{filters['transmission']}%")

    if filters.get("fuel"):
        query += " AND fuel ILIKE %s"
        params.append(f"%{filters['fuel']}%")

    if filters.get("year"):
        query += " AND year = %s"
        params.append(str(filters["year"]))

    if filters.get("max_km"):
        query += " AND CAST(km_driven AS INTEGER) <= %s"
        params.append(filters["max_km"])

    if filters.get("brand") or filters.get("model"):
        search_term = filters.get("brand") or filters.get("model")
        query += " AND title ILIKE %s"
        params.append(f"%{search_term}%")

    try:
        conn   = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("Filters received:", filters)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        ids = [str(row[0]) for row in rows]
        print(f"PostgreSQL returned {len(ids)} IDs")
        return ids

    except Exception as e:
        print(f"PostgreSQL query failed: {e}")
        return []


# ─────────────────────────────
# STEP 2 — CHROMADB SEARCH
# ─────────────────────────────

def query_chroma(question: str, postgres_ids: list, top_k: int = 5) -> list:

    question_vector = embedding_model.encode(question).tolist()

    try:
        if postgres_ids:
            results = chroma_collection.query(
                query_embeddings=[question_vector],
                n_results=min(top_k, len(postgres_ids)),
                ids=postgres_ids
            )
        else:
            results = chroma_collection.query(
                query_embeddings=[question_vector],
                n_results=top_k
            )

        top_ids = results["ids"][0]
        print(f"Chroma returned {len(top_ids)} IDs")
        return top_ids

    except Exception as e:
        print(f"ChromaDB query failed: {e}")
        return postgres_ids[:top_k] if postgres_ids else []


# ─────────────────────────────
# STEP 3 — FETCH FULL DETAILS
# ─────────────────────────────

def fetch_listings_by_ids(ids: list) -> list:

    if not ids:
        return []

    try:
        conn   = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        int_ids = [int(i) for i in ids]

        cursor.execute("""
            SELECT id, title, price_pkr, price_lakh, city, year,
                   km_driven, fuel, transmission, description, url
            FROM listings
            WHERE id = ANY(%s)
            ORDER BY array_position(%s, id)   -- ✅ PRESERVE ORDER
        """, (int_ids, int_ids))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        listings = []
        for row in rows:
            listings.append({
                "id":           row[0],
                "title":        row[1],
                "price_pkr":    row[2],
                "price_lakh":   row[3],
                "city":         row[4],
                "year":         row[5],
                "km_driven":    row[6],
                "fuel":         row[7],
                "transmission": row[8],
                "description":  row[9],
                "url":          row[10]
            })

        return listings

    except Exception as e:
        print(f"Fetch listings failed: {e}")
        return []


# ─────────────────────────────
# MAIN RETRIEVE FUNCTION
# ─────────────────────────────

def retrieve(question: str, filters: dict, top_k: int = 5) -> list:

    # ✅ If no filters → skip SQL filtering
    if not filters:
        postgres_ids = []
    else:
        postgres_ids = query_postgres(filters)

    # semantic search
    top_ids = query_chroma(question, postgres_ids, top_k)

    # fetch full data
    listings = fetch_listings_by_ids(top_ids)

    #  REMOVE DUPLICATES 
    seen_urls = set()
    unique_listings = []

    for l in listings:
        url = l.get("url")
        if url and url not in seen_urls:
            unique_listings.append(l)
            seen_urls.add(url)

    print(f"Final unique listings: {len(unique_listings)}")

    return unique_listings


# ─────────────────────────────
# TEST
# ─────────────────────────────

if __name__ == "__main__":
    question = "family car under 40 lakh in Lahore"
    filters = {
        "max_price": 4000000,
        "city": "Lahore"
    }

    results = retrieve(question, filters)

    for r in results:
        print(f"{r['title']} | {r['price_lakh']} | {r['city']}")
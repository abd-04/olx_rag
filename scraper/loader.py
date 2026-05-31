import json
import os
from pathlib import Path

import chromadb
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

SCRAPER_DIR = Path(__file__).resolve().parent
load_dotenv(SCRAPER_DIR.parent / ".env")

INPUT_FILE = SCRAPER_DIR / "data" / "clean_listings.json"
CHROMA_PATH = os.getenv("CHROMA_PATH", str(SCRAPER_DIR / "chroma_data"))
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "olxdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}
DATABASE_URL = os.getenv("DATABASE_URL")


def connect_postgres():
    connection = psycopg2.connect(DATABASE_URL) if DATABASE_URL else psycopg2.connect(**DB_CONFIG)
    print("Connected to PostgreSQL")
    return connection


def connect_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="olx_listings",
        metadata={"hnsw:space": "cosine"},
    )
    print("Connected to ChromaDB")
    return collection


def create_table(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                price_pkr BIGINT NOT NULL,
                price_lakh TEXT,
                city TEXT,
                year TEXT,
                km_driven TEXT,
                fuel TEXT,
                transmission TEXT,
                vehicle_type TEXT NOT NULL DEFAULT 'car',
                engine_cc TEXT,
                description TEXT,
                url TEXT NOT NULL UNIQUE,
                embedding_text TEXT NOT NULL
            );
        """)
        cursor.execute("ALTER TABLE listings ADD COLUMN IF NOT EXISTS vehicle_type TEXT NOT NULL DEFAULT 'car';")
        cursor.execute("ALTER TABLE listings ADD COLUMN IF NOT EXISTS engine_cc TEXT;")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS listings_url_idx ON listings (url);")
        cursor.execute("CREATE INDEX IF NOT EXISTS listings_price_idx ON listings (price_pkr);")
        cursor.execute("CREATE INDEX IF NOT EXISTS listings_vehicle_type_idx ON listings (vehicle_type);")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS listings_search_idx ON listings USING GIN (
                to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, ''))
            );
        """)
    connection.commit()


def upsert_postgres(cursor, listing):
    cursor.execute("""
        INSERT INTO listings (
            title, price_pkr, price_lakh, city, year, km_driven, fuel,
            transmission, vehicle_type, engine_cc, description, url,
            embedding_text
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            price_pkr = EXCLUDED.price_pkr,
            price_lakh = EXCLUDED.price_lakh,
            city = EXCLUDED.city,
            year = EXCLUDED.year,
            km_driven = EXCLUDED.km_driven,
            fuel = EXCLUDED.fuel,
            transmission = EXCLUDED.transmission,
            vehicle_type = EXCLUDED.vehicle_type,
            engine_cc = EXCLUDED.engine_cc,
            description = EXCLUDED.description,
            embedding_text = EXCLUDED.embedding_text
        RETURNING id;
    """, (
        listing.get("title") or "Untitled listing",
        listing["price_pkr"],
        listing.get("price_lakh"),
        listing.get("city"),
        listing.get("year"),
        listing.get("km_driven"),
        listing.get("fuel"),
        listing.get("transmission"),
        listing.get("vehicle_type") or "car",
        listing.get("engine_cc"),
        listing.get("description"),
        listing["url"],
        listing.get("embedding_text") or "",
    ))
    return cursor.fetchone()[0]


def upsert_chroma(collection, row_id, embedding, listing):
    collection.upsert(
        ids=[str(row_id)],
        embeddings=[embedding],
        metadatas=[{
            "title": listing.get("title") or "",
            "city": listing.get("city") or "",
            "price_pkr": listing.get("price_pkr") or 0,
            "year": listing.get("year") or "",
            "vehicle_type": listing.get("vehicle_type") or "car",
            "url": listing.get("url") or "",
        }],
    )


def delete_stale_listings(connection, collection, active_urls):
    """Remove listings that disappeared from the latest cleaned snapshot."""
    if not active_urls:
        raise ValueError("Refusing to prune listings from an empty input dataset.")

    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM listings WHERE NOT (url = ANY(%s));", (active_urls,))
        stale_ids = [str(row[0]) for row in cursor.fetchall()]
        cursor.execute("DELETE FROM listings WHERE NOT (url = ANY(%s));", (active_urls,))
    connection.commit()

    if stale_ids:
        collection.delete(ids=stale_ids)
        print(f"Removed stale listings: {len(stale_ids)}")


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        listings = json.load(file)

    print(f"Loaded {len(listings)} listings from {INPUT_FILE}")
    connection = connect_postgres()
    collection = connect_chroma()
    model = SentenceTransformer(EMBEDDING_MODEL)
    create_table(connection)
    delete_stale_listings(connection, collection, [listing["url"] for listing in listings])

    success = 0
    failed = 0
    with connection.cursor() as cursor:
        for index, listing in enumerate(listings, start=1):
            try:
                row_id = upsert_postgres(cursor, listing)
                embedding = model.encode(listing.get("embedding_text", "")).tolist()
                upsert_chroma(collection, row_id, embedding, listing)
                connection.commit()
                success += 1
                if index % 10 == 0:
                    print(f"Progress: {index}/{len(listings)} upserted")
            except Exception as error:
                connection.rollback()
                failed += 1
                print(f"Failed on listing {index}: {error}")

    connection.close()
    print(f"Successfully loaded : {success}")
    print(f"Failed              : {failed}")


if __name__ == "__main__":
    load_data()

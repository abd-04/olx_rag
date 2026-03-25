import json
import os
import psycopg2                                    # connects to PostgreSQL
from sentence_transformers import SentenceTransformer  # converts text to vectors
import chromadb                                    # vector database

INPUT_FILE = "data/clean_listings.json"

# ─────────────────────────────
# POSTGRESQL CONNECTION
# ─────────────────────────────

# change password to whatever you set during PostgreSQL installation
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "olxdb",
    "user":     "postgres",
    "password": "pakistan"    # ← change this to your password
}


def connect_postgres():
    """
    Creates and returns a PostgreSQL connection.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected to PostgreSQL")
    return conn


# ─────────────────────────────
# CHROMADB CONNECTION
# ─────────────────────────────

def connect_chroma():
    """
    Creates and returns a ChromaDB client.
    Saves vector files locally in chroma_data/ folder.
    No server needed — runs entirely as local files.
    """
    client = chromadb.PersistentClient(path="chroma_data")
    collection = client.get_or_create_collection(
        name="olx_listings",
        metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
    )
    print("Connected to ChromaDB")
    return collection


# ─────────────────────────────
# CREATE POSTGRESQL TABLE
# ─────────────────────────────

def create_table(conn):
    """
    Creates the listings table in PostgreSQL if it doesn't exist.
    Safe to run multiple times — won't delete existing data.
    """
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id            SERIAL PRIMARY KEY,
            title         TEXT,
            price_pkr     BIGINT,
            price_lakh    TEXT,
            city          TEXT,
            year          TEXT,
            km_driven     TEXT,
            fuel          TEXT,
            transmission  TEXT,
            description   TEXT,
            url           TEXT,
            embedding_text TEXT
        );
    """)

    conn.commit()
    cursor.close()
    print("PostgreSQL table ready")


# ─────────────────────────────
# INSERT ONE LISTING INTO POSTGRESQL
# ─────────────────────────────

def insert_into_postgres(cursor, listing):
    """
    Inserts one listing into PostgreSQL.
    Returns the auto-generated ID of the inserted row.
    This ID will be used in ChromaDB too so both DBs stay in sync.
    """
    cursor.execute("""
        INSERT INTO listings (
            title, price_pkr, price_lakh, city, year,
            km_driven, fuel, transmission, description,
            url, embedding_text
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        listing.get("title"),
        listing.get("price_pkr"),
        listing.get("price_lakh"),
        listing.get("city"),
        listing.get("year"),
        listing.get("km_driven"),
        listing.get("fuel"),
        listing.get("transmission"),
        listing.get("description"),
        listing.get("url"),
        listing.get("embedding_text")
    ))

    # RETURNING id gives us back the auto generated row ID
    row_id = cursor.fetchone()[0]
    return row_id


# ─────────────────────────────
# INSERT ONE LISTING INTO CHROMADB
# ─────────────────────────────

def insert_into_chroma(collection, row_id, embedding, listing):
    """
    Inserts one listing vector into ChromaDB.
    Uses the same ID as PostgreSQL row so they can be matched later.
    Also stores basic metadata for filtering if needed.
    """
    collection.add(
        ids=[str(row_id)],          # must be string in ChromaDB
        embeddings=[embedding],     # the vector from sentence-transformers
        metadatas=[{                # basic metadata stored alongside vector
            "title":        listing.get("title", ""),
            "city":         listing.get("city") or "",
            "price_pkr":    listing.get("price_pkr") or 0,
            "price_lakh":   listing.get("price_lakh") or "",
            "year":         listing.get("year") or "",
            "url":          listing.get("url") or ""
        }]
    )


# ─────────────────────────────
# MAIN LOADER FUNCTION
# ─────────────────────────────

def load_data():

    # read clean listings from cleaner.py output
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        listings = json.load(f)

    print(f"Loaded {len(listings)} listings from {INPUT_FILE}")

    # connect to both databases
    conn       = connect_postgres()
    collection = connect_chroma()

    # load the sentence transformer model
    # this model converts text to vectors
    # downloads automatically on first run (~90MB)
    print("Loading embedding model...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print("Embedding model ready")

    # create PostgreSQL table if not exists
    create_table(conn)

    cursor = conn.cursor()

    success = 0
    failed  = 0

    for i, listing in enumerate(listings):

        try:
            # step 1 — insert into PostgreSQL, get back the row ID
            row_id = insert_into_postgres(cursor, listing)

            # step 2 — convert embedding_text to vector
            embedding_text = listing.get("embedding_text", "")
            embedding = model.encode(embedding_text).tolist()
            # .tolist() converts numpy array to plain Python list
            # ChromaDB needs a plain list not numpy array

            # step 3 — insert vector into ChromaDB with same ID
            insert_into_chroma(collection, row_id, embedding, listing)

            success += 1

            # commit every 10 listings so we don't lose everything if it crashes
            if i % 10 == 0:
                conn.commit()
                print(f"  Progress: {i+1}/{len(listings)} inserted")

        except Exception as e:
            failed += 1
            print(f"  Failed on listing {i+1}: {e}")
            continue

    # final commit
    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nDone.")
    print(f"Successfully loaded : {success}")
    print(f"Failed              : {failed}")
    print(f"PostgreSQL          : olxdb → listings table")
    print(f"ChromaDB            : chroma_data/ folder")


if __name__ == "__main__":
    load_data()
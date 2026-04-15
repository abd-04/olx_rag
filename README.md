# OLX Vehicle Finder 

A RAG-powered assistant for searching used cars and bikes on OLX Pakistan.
Ask questions in plain English or Roman Urdu and get intelligent answers
backed by real OLX listings.

---

## What it does

Instead of scrolling through hundreds of OLX ads, just ask:

- *"family car under 30 lakh in Lahore"*
- *"honda civic good condition low mileage"*
- *"125cc bike under 2 lakh"*
- *"gari chahiye jo theek ho aur kaam na kare"*

The app searches through 400 real OLX listings using hybrid retrieval
and gives you a conversational recommendation with direct links.

---

## Architecture
```
User Question
      ↓
LLM extracts filters (Groq - llama3.3-70b)
      ↓
PostgreSQL — SQL filter on city, price, brand, year
      ↓
ChromaDB — semantic vector search on listing descriptions
      ↓
Top 5 listings → LLM generates answer
      ↓
Streamlit UI shows answer + listing cards
```

**Hybrid Retrieval** — combines SQL filtering (structured fields)
with semantic vector search (meaning and context).
Each listing description is embedded using
`paraphrase-multilingual-MiniLM-L12-v2` which supports
English and Roman Urdu.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Selenium  |
| Structured DB | PostgreSQL |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| Backend API | FastAPI |
| LLM | Groq (llama-3.3-70b-versatile) |
| Frontend | Streamlit |


---

## Project Structure
```
olx-rag-app/
├── docker-compose.yml
├── .env
├── scraper/
│   ├── scraper_v2.py       # scrapes OLX listings
│   ├── cleaner.py          # cleans and normalizes data
│   ├── loader.py           # loads into PostgreSQL + ChromaDB
│   └── data/
│       ├── raw_listings.json
│       └── clean_listings.json
├── backend/
│   ├── main.py             # FastAPI app
│   ├── retriever.py        # hybrid SQL + vector retrieval
│   └── llm.py              # Groq API calls
├── frontend/
│   └── app.py              # Streamlit UI
└── database/
    └── init.sql            # PostgreSQL schema
```




## What each file does:

The project is split into a few stages: scraping → cleaning → loading → retrieval → answering.

### Scraping (`scraper_v2.py`, `scraper_v3.py`)

I started by collecting data directly from OLX.

* `scraper_v2.py` scrapes around 30–35 pages from the cars section.
* To add more variety (and make the dataset less “perfect”), I also scraped bikes using `scraper_v3.py`.

The idea was to work with messy, real-world data instead of a clean dataset, since that’s what most real systems deal with.

---

### Cleaning (`cleaner.py`)

The raw scraped data was quite inconsistent:

* Missing or incomplete fields
* Prices in different formats (lakh, PKR, text)
* Mixed language descriptions (English + Roman Urdu)

The `cleaner.py` script processes this and produces a clean, structured dataset:

* Standardizes important fields (price, year, km driven, etc.)
* Removes broken or unusable entries
* Outputs a consistent `clean_listings.json`

This becomes the main dataset used by the system.

---

### Loading (`loader.py`)

This is where the data is actually prepared for search.

The loader does two things at the same time:

#### 1. Store structured data in PostgreSQL

Each listing is inserted into a PostgreSQL table with fields like:

* title
* price
* city
* year
* fuel
* transmission
* description
* url

This allows traditional filtering like:

* “under 20 lakh”
* “in Lahore”
* “automatic cars”

---

#### 2. Create embeddings and store in ChromaDB

I added a field called `embedding_text`.

Instead of embedding each column separately, I combine the key details of a listing into a short sentence-like format. This gives better semantic meaning compared to raw structured fields.

That text is then converted into a vector using a sentence transformer model.

* The vector → stored in ChromaDB
* The original data → stored in PostgreSQL

So each listing exists in two forms:

* Structured (Postgres)
* Semantic (ChromaDB)

---

## Backend (Core Logic)

The backend is where everything connects together. It handles:

* understanding the user query
* retrieving relevant listings
* generating a natural response

---

### API Layer (`main.py`)

This is a FastAPI server that exposes the main endpoint:

```
POST /ask
```

Flow:

1. User sends a question
2. Backend processes it
3. Returns:

   * generated answer
   * top listings
   * extracted filters

It basically acts as the bridge between the frontend and the retrieval system.

---

### LLM Logic (`llm.py`)

This file handles all interaction with the language model.

There are two main tasks:

#### 1. Extracting filters

The model converts a natural query into structured filters.

Example:

```
"car under 20 lakh in lahore"
→ { "max_price": 2000000, "city": "Lahore" }
```

This allows the system to use SQL effectively instead of guessing.

---

#### 2. Generating answers

After retrieval, the LLM:

* looks at the top listings
* writes a short, natural response
* includes useful suggestions and links

The goal here was to make it feel less like a search engine and more like someone helping you choose.

---

### Retrieval (`retriever.py`)

This is the most important part of the system.

Instead of relying only on keywords or only on vectors, I used a hybrid approach.

#### Step 1 — SQL filtering

Based on extracted filters, PostgreSQL is queried:

* brand
* city
* price range
* fuel type
* etc.

This narrows down the dataset.

---

#### Step 2 — Semantic search (ChromaDB)

The user query is converted into an embedding and compared against stored vectors.

This helps match intent, not just keywords.

For example:

* “family car”
* “reliable car”
* “fuel efficient”

These don’t rely on exact matches in the database.

---

#### Step 3 — Combine results

The system combines:

* filtered results (Postgres)
* semantic matches (Chroma)

and returns the most relevant listings.

---

## Why this approach

Using only SQL would make the system too rigid.
Using only embeddings would ignore useful structured filters.

Combining both gives:

* precision (filters)
* flexibility (semantic search)

This is essentially a simple implementation of a Retrieval-Augmented Generation (RAG) system.

---

## Summary

* Data is scraped from OLX
* Cleaned into a usable dataset
* Stored in PostgreSQL (structured)
* Embedded and stored in ChromaDB (semantic)
* Retrieved using a hybrid search approach
* Passed to an LLM to generate a natural answer

---








# OLX Vehicle Finder 🚗

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
| Scraping | Selenium + BeautifulSoup |
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

---

## How to run locally

### Prerequisites
- Docker Desktop installed and running
- Groq API key (free at console.groq.com)

### 1. Clone the repo
```bash
git clone https://github.com/[YOUR_USERNAME]/olx-rag-app.git
cd olx-rag-app
```

### 2. Set up environment variables

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=olxdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Start all services
```bash
docker compose up --build
```

### 4. Load data into the database

In a new terminal:
```bash
cd scraper
pip install -r requirements.txt
python loader.py
```

### 5. Open the app
```
http://localhost:8501
```

---

## Data Pipeline
```
scraper_v2.py   →   raw_listings.json
cleaner.py      →   clean_listings.json
loader.py       →   PostgreSQL + ChromaDB
```

Scraped [X] listings from OLX Pakistan (cars and bikes).
After cleaning [X] listings were retained.
Each listing's title + description is embedded and stored
in ChromaDB for semantic search.

---

## Live Demo

[Add your Railway/Render backend URL here]
[Add your Streamlit Cloud URL here]

---

## Author


```

---


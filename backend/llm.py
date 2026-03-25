import os
import json
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


# ─────────────────────────────
# JOB 1 — EXTRACT FILTERS
# ─────────────────────────────

def extract_filters(question: str) -> dict:

    prompt = f"""
You are a car listing filter extractor for a Pakistani used car platform.

Extract search filters from the user question below.

Return ONLY a valid JSON object. If nothing is found, return {{}}.
Do NOT return any explanation or text.

Possible fields:
- city (string)
- max_price (integer, in PKR)
- min_price (integer, in PKR)
- brand (string)
- model (string)
- year (string)
- transmission (Manual or Automatic)
- fuel (Petrol, Diesel, Hybrid)
- max_km (integer)
- vehicle_type (car or bike)
- engine_cc (string)

Rules:
- Convert lakh to PKR (1 lakh = 100000)
- Only include fields explicitly mentioned

User question: {question}

JSON:
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            filters = json.loads(raw)
        except:
            print("⚠️ JSON parse failed. Raw output:", raw)
            filters = {}

        return filters

    except Exception as e:
        print(f"Filter extraction failed: {e}")
        return {}


# ─────────────────────────────
# JOB 2 — GENERATE ANSWER
# ─────────────────────────────

def generate_answer(question: str, listings: list) -> str:

    if not listings:
        return "Sorry, I couldn’t find any good matches for that. Try adjusting your filters a bit."

    #  remove duplicates
    seen = set()
    unique_listings = []

    for l in listings:
        url = l.get("url")
        if url and url not in seen:
            unique_listings.append(l)
            seen.add(url)

    listings = unique_listings[:5]  # keep top 5

    # ✅ clean listing format (no "Listing 1")
    listings_text = ""
    for listing in listings:
        listings_text += f"""
Title: {listing.get('title', '')}
Price: {listing.get('price_lakh', '')}
City: {listing.get('city', '')}
Year: {listing.get('year', '')}
KM: {listing.get('km_driven', '')}
Fuel: {listing.get('fuel', '')}
Transmission: {listing.get('transmission', '')}
URL: {listing.get('url', '')}

"""

    prompt = f"""
You are a helpful car buying assistant for OLX Pakistan.

Talk like a real person helping a friend.

Keep it short, natural, and useful.

What to do:
- Recommend the best 1–2 options clearly
- Briefly mention other decent options
- Don’t over-explain

Rules:
- No numbering like "Listing 1"
- No robotic tone
- No repeating same listing
- Match user's language (Roman Urdu or English)

End with:
Listing Links:
- include exactly 3 unique and relevant URLs

Listings:
{listings_text}

User question: {question}

Answer:
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Answer generation failed: {e}")
        return "Sorry, something went wrong while generating the answer."
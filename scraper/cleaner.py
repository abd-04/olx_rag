import json
import re

INPUT_FILE  = "data/raw_listings.json"
OUTPUT_FILE = "data/clean_listings.json"


# ─────────────────────────────
# PRICE EXTRACTION
# ─────────────────────────────

def extract_price_from_text(text):
    if not text:
        return None

    text = text.lower().replace(",", "")

    lakh_match = re.search(r"([\d.]+)\s*(lakh|lac|lacs)", text)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 100000)

    crore_match = re.search(r"([\d.]+)\s*crore", text)
    if crore_match:
        return int(float(crore_match.group(1)) * 10000000)

    pkr_match = re.search(r"(?:pkr|rs\.?)\s*([\d]+)", text)
    if pkr_match:
        value = int(pkr_match.group(1))
        if 100000 <= value <= 100000000:
            return value

    return None


def convert_price(listing):
    price = extract_price_from_text(listing.get("price_text", ""))
    if price:
        return price

    price = extract_price_from_text(listing.get("description", ""))
    if price:
        return price

    return None


# ─────────────────────────────
# CITY EXTRACTION
# ─────────────────────────────

CITIES = [
    "karachi", "lahore", "islamabad", "rawalpindi", "peshawar",
    "quetta", "multan", "faisalabad", "sialkot", "gujranwala",
    "hyderabad", "abbottabad", "murree", "sahiwal", "bahawalpur",
    "sargodha", "sheikhupura", "larkana", "sukkur", "mardan",
    "wazirabad", "gujrat", "jhelum", "attock", "chakwal",
    "mingora", "dera ghazi khan", "rahim yar khan"
]


def extract_city(listing):
    city_raw = listing.get("city", "")
    if city_raw:
        cleaned = city_raw.split(",")[-1].strip()
        if cleaned and not re.match(r"^[\d,\.]+$", cleaned):
            return cleaned

    description = listing.get("description", "").lower()
    for city in CITIES:
        if re.search(rf"\b{city}\b", description):
            return city.capitalize()

    return None


# ─────────────────────────────
# BUILD EMBEDDING TEXT (FIXED)
# ─────────────────────────────

def build_embedding_text(listing):
    """
    SHORT + STRUCTURED text for embeddings
    (No long descriptions, no noise)
    """

    parts = []

    title = listing.get("title", "")
    city = listing.get("city", "")
    year = listing.get("year", "")
    fuel = listing.get("fuel", "")
    transmission = listing.get("transmission", "")
    price = listing.get("price_lakh", "")
    km = listing.get("km_driven", "")

    if title:
        parts.append(title)

    if city:
        parts.append(city)

    if year:
        parts.append(str(year))

    if fuel:
        parts.append(fuel)

    if transmission:
        parts.append(transmission)

    if price:
        parts.append(price)

    if km:
        parts.append(f"{km} km")

    # optional semantic hints (boosts search)
    parts.append("car vehicle")

    return " | ".join(parts).lower()


# ─────────────────────────────
# CLEAN SINGLE LISTING
# ─────────────────────────────

def clean_listing(raw):

    price = convert_price(raw)

    if price is None:
        return None

    city = extract_city(raw)

    price_in_lakh = round(price / 100000, 2)
    price_lakh_str = f"{price_in_lakh} lakh"

    cleaned = {
        "title":          raw.get("title", "").strip(),
        "price_pkr":      price,
        "price_lakh":     price_lakh_str,
        "city":           city,
        "year":           raw.get("year", ""),
        "km_driven":      raw.get("km_driven", ""),
        "fuel":           raw.get("fuel", ""),
        "transmission":   raw.get("transmission", ""),
        "description":    raw.get("description", "").strip(),
        "url":            raw.get("url", ""),
        "embedding_text": ""   # filled below
    }

    # build embedding AFTER cleaning
    cleaned["embedding_text"] = build_embedding_text(cleaned)

    return cleaned


# ─────────────────────────────
# MAIN (WITH DEDUP)
# ─────────────────────────────

def clean_data():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        listings = json.load(f)

    cleaned = []
    skipped = 0

    seen_urls = set()

    for listing in listings:
        result = clean_listing(listing)

        if not result:
            skipped += 1
            continue

        url = result.get("url")

        if url and url not in seen_urls:
            cleaned.append(result)
            seen_urls.add(url)

    print(f"Original listings : {len(listings)}")
    print(f"Clean listings    : {len(cleaned)}")
    print(f"Skipped           : {skipped}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Saved to          : {OUTPUT_FILE}")


if __name__ == "__main__":
    clean_data()
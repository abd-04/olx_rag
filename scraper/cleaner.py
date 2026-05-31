import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
INPUT_FILE = DATA_DIR / "raw_listings.json"
OUTPUT_FILE = DATA_DIR / "clean_listings.json"

CITIES = [
    "karachi", "lahore", "islamabad", "rawalpindi", "peshawar",
    "quetta", "multan", "faisalabad", "sialkot", "gujranwala",
    "hyderabad", "abbottabad", "murree", "sahiwal", "bahawalpur",
    "sargodha", "sheikhupura", "larkana", "sukkur", "mardan",
    "wazirabad", "gujrat", "jhelum", "attock", "chakwal",
    "mingora", "dera ghazi khan", "rahim yar khan",
]


def extract_price_from_text(text):
    if not text:
        return None

    text = str(text).lower().replace(",", "")
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*\.?\s*(lakh|lac|lacs)", text)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 100000)

    crore_match = re.search(r"(\d+(?:\.\d+)?)\s*\.?\s*crore", text)
    if crore_match:
        return int(float(crore_match.group(1)) * 10000000)

    pkr_match = re.search(r"(?:pkr|rs\.?)\s*([\d]+)", text)
    if pkr_match:
        value = int(pkr_match.group(1))
        if 10000 <= value <= 100000000:
            return value

    return None


def convert_price(listing, vehicle_type):
    existing_price = listing.get("price_pkr")
    minimum_price = 10000 if vehicle_type == "bike" else 100000
    if isinstance(existing_price, (int, float)) and minimum_price <= existing_price <= 100000000:
        return int(existing_price)

    recovered_price = (
        extract_price_from_text(listing.get("price_text", ""))
        or extract_price_from_text(listing.get("description", ""))
    )
    return recovered_price if recovered_price and minimum_price <= recovered_price <= 100000000 else None


def extract_city(listing):
    city_raw = listing.get("city", "")
    if city_raw:
        cleaned = str(city_raw).split(",")[-1].strip()
        if cleaned and not re.match(r"^[\d,.]+$", cleaned):
            return cleaned

    description = listing.get("description", "").lower()
    for city in CITIES:
        if re.search(rf"\b{re.escape(city)}\b", description):
            return city.title()

    return None


def first_value(listing, *keys):
    lowered = {str(key).lower().strip(): value for key, value in listing.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def normalize_vehicle_type(listing):
    category = first_value(listing, "category").lower()
    if "bike" in category or "motorcycle" in category:
        return "bike"
    return "car"


def build_embedding_text(listing):
    """Create a concise but semantically useful listing representation."""
    parts = [
        listing.get("vehicle_type", ""),
        listing.get("title", ""),
        listing.get("city", ""),
        listing.get("year", ""),
        listing.get("fuel", ""),
        listing.get("transmission", ""),
        listing.get("engine_cc", ""),
        listing.get("price_lakh", ""),
        f"{listing.get('km_driven')} km" if listing.get("km_driven") else "",
        listing.get("description", "")[:800],
    ]
    return " | ".join(str(part) for part in parts if part).lower()


def clean_listing(raw):
    vehicle_type = normalize_vehicle_type(raw)
    price = convert_price(raw, vehicle_type)
    url = str(raw.get("url", "")).strip()
    if price is None or not url:
        return None

    cleaned = {
        "title": str(raw.get("title", "")).strip(),
        "price_pkr": price,
        "price_lakh": f"{round(price / 100000, 2)} lakh",
        "city": extract_city(raw),
        "year": first_value(raw, "year"),
        "km_driven": first_value(raw, "km_driven", "km driven"),
        "fuel": first_value(raw, "fuel"),
        "transmission": first_value(raw, "transmission"),
        "vehicle_type": vehicle_type,
        "engine_cc": first_value(raw, "engine_cc", "engine capacity", "engine"),
        "description": str(raw.get("description", "")).strip(),
        "url": url,
        "embedding_text": "",
    }
    cleaned["embedding_text"] = build_embedding_text(cleaned)
    return cleaned


def clean_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        listings = json.load(file)

    cleaned_by_url = {}
    skipped = 0
    for listing in listings:
        result = clean_listing(listing)
        if result:
            cleaned_by_url[result["url"]] = result
        else:
            skipped += 1

    cleaned = list(cleaned_by_url.values())
    print(f"Original listings : {len(listings)}")
    print(f"Clean listings    : {len(cleaned)}")
    print(f"Skipped           : {skipped}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(cleaned, file, indent=2, ensure_ascii=False)

    print(f"Saved to          : {OUTPUT_FILE}")


if __name__ == "__main__":
    clean_data()

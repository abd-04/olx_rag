import time
import json
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ── CONFIG ─────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.olx.com.pk"

# bikes category URL
CATEGORY_URL = "https://www.olx.com.pk/motorcycles_c81"

# same raw file as cars — we APPEND not overwrite
RAW_FILE = "data/raw_listings.json"


# ── SELENIUM SETUP ─────────────────────────────────────────────────────────────

def get_driver():
    """
    Creates and returns a headless Chrome browser.
    Headless means no browser window opens — runs silently.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


# ── STEP 1 — GET LISTING LINKS FROM ONE PAGE ───────────────────────────────────

def get_listing_links(driver, page_url):
    """
    Opens a category page.
    Returns list of individual listing URLs found on that page.
    """
    driver.get(page_url)
    time.sleep(3)

    links = []
    items = driver.find_elements(By.CSS_SELECTOR, "a[href*='/item/']")

    for item in items:
        href = item.get_attribute("href")
        if href and "/item/" in href:
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in links:
                links.append(full_url)

    print(f"    Found {len(links)} listings on this page")
    return links


# ── STEP 2 — SCRAPE ONE LISTING ────────────────────────────────────────────────

def scrape_listing(driver, url):
    """
    Opens a single listing page.
    Extracts all available fields.
    Returns a dictionary or None if failed.
    """
    try:
        driver.get(url)
        time.sleep(2)

        # title
        try:
            title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            title = ""

        # price
        try:
            price_el = driver.find_element(By.CSS_SELECTOR, "h3")
            price_text = price_el.text.strip()
        except:
            price_text = ""

        # description
        try:
            desc_el = driver.find_element(
                By.CSS_SELECTOR, "div[aria-label='Description']"
            )
            description = desc_el.text.strip()
        except:
            description = ""

        # location
        try:
            loc_els = driver.find_elements(By.CSS_SELECTOR, "span")
            location = ""
            for el in loc_els:
                text = el.text.strip()
                if "," in text and len(text) < 60:
                    location = text
                    break
        except:
            location = ""

        # date posted
        try:
            date_els = driver.find_elements(By.CSS_SELECTOR, "span")
            date_posted = ""
            for el in date_els:
                text = el.text.strip()
                if "ago" in text.lower() or "today" in text.lower():
                    date_posted = text
                    break
        except:
            date_posted = ""

        # extra details (engine, brand, model etc)
        details = {}
        try:
            items = driver.find_elements(By.CSS_SELECTOR, "li")
            for item in items:
                text = item.text.strip()
                if ":" in text:
                    parts = text.split(":", 1)
                    if len(parts) == 2:
                        key   = parts[0].strip()
                        value = parts[1].strip()
                        if key and value and len(key) < 40:
                            details[key] = value
        except:
            pass

        listing = {
            "title":       title,
            "price_text":  price_text,
            "city":        location,
            "date_posted": date_posted,
            "description": description,
            "url":         url,
            "category":    "bikes",    # tag so we know it's a bike listing
            **details
        }

        return listing

    except Exception as e:
        print(f"    Failed: {url} → {e}")
        return None


# ── STEP 3 — SCRAPE MULTIPLE PAGES ────────────────────────────────────────────

def scrape_bikes(max_pages=20):
    """
    Scrapes bikes category across multiple pages.
    Returns list of raw listing dicts.
    """
    all_listings = []
    driver = get_driver()

    try:
        for page_num in range(1, max_pages + 1):

            # OLX pagination: ?page=2, ?page=3 etc
            if page_num == 1:
                page_url = CATEGORY_URL
            else:
                page_url = f"{CATEGORY_URL}?page={page_num}"

            print(f"\nScraping bikes page {page_num}...")
            links = get_listing_links(driver, page_url)

            for i, link in enumerate(links):
                print(f"  Listing {i+1}/{len(links)}")
                listing = scrape_listing(driver, link)
                if listing:
                    all_listings.append(listing)
                time.sleep(1)

            time.sleep(2)

    finally:
        driver.quit()

    return all_listings


# ── STEP 4 — APPEND TO EXISTING RAW JSON ──────────────────────────────────────

def append_to_raw_file(new_listings, filepath):
    """
    Reads existing raw_listings.json.
    Appends new bike listings to it.
    Saves back to the same file.
    This way car + bike listings are all in one file.
    """
    # load existing listings
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except:
                existing = []

    print(f"\nExisting listings in file : {len(existing)}")
    print(f"New bike listings scraped : {len(new_listings)}")

    # combine
    combined = existing + new_listings

    # save back
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Total listings in file    : {len(combined)}")
    print(f"Saved to                  : {filepath}")


# ── RUN ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting OLX bikes scraper...")
    print(f"Category : bikes")
    print(f"Output   : {RAW_FILE} (appending)")
    print("-" * 50)

    listings = scrape_bikes(max_pages=15)
    print(f"\nTotal bike listings scraped: {len(listings)}")

    append_to_raw_file(listings, RAW_FILE)

    print("\nDone. Next step: re-run cleaner.py then loader.py")
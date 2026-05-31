import time
import json
import os
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


BASE_URL = "https://www.olx.com.pk/cars_c84"
OUTPUT_FILE = Path(__file__).resolve().parent / "data" / "raw_listings.json"

MAX_PAGES = 25
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")


# ─────────────────────────────────────────────
# DRIVER
# ─────────────────────────────────────────────

def start_driver():

    options = webdriver.ChromeOptions()

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver_path = CHROMEDRIVER_PATH if os.path.exists(CHROMEDRIVER_PATH) else ChromeDriverManager().install()
    driver = webdriver.Chrome(
        service=Service(driver_path),
        options=options
    )

    return driver


# ─────────────────────────────────────────────
# PRICE CONVERTER
# ─────────────────────────────────────────────

def convert_price(price_text):

    if not price_text:
        return None

    text = price_text.lower()
    text = text.replace("rs", "").replace(",", "").strip()

    numbers = re.findall(r"\d+\.?\d*", text)

    if not numbers:
        return None

    value = float(numbers[0])

    if "lac" in text or "lakh" in text:
        return int(value * 100000)

    if "crore" in text:
        return int(value * 10000000)

    return int(value)


# ─────────────────────────────────────────────
# CITY EXTRACTOR
# ─────────────────────────────────────────────

def extract_city(location_text):

    if not location_text:
        return None

    parts = location_text.split(",")

    return parts[-1].strip()


# ─────────────────────────────────────────────
# GET LISTING LINKS
# ─────────────────────────────────────────────

def get_listing_links(driver):

    links = []

    elements = driver.find_elements(By.XPATH, "//a[contains(@href,'/item/')]")

    for el in elements:

        href = el.get_attribute("href")

        if href and href not in links:

            links.append(href)

    print("Listings found:", len(links))

    return links


# ─────────────────────────────────────────────
# EXTRACT VEHICLE SPECS
# ─────────────────────────────────────────────

def extract_specs(driver):

    specs = {
        "year": None,
        "km_driven": None,
        "fuel": None,
        "transmission": None
    }

    try:

        rows = driver.find_elements(By.XPATH, "//span[contains(text(),'Year')]/following::span[1]")

        if rows:
            specs["year"] = rows[0].text

    except:
        pass

    try:

        km = driver.find_element(By.XPATH, "//span[contains(text(),'KM')]/following::span[1]")

        specs["km_driven"] = km.text.replace(",", "")

    except:
        pass

    try:

        fuel = driver.find_element(By.XPATH, "//span[contains(text(),'Fuel')]/following::span[1]")

        specs["fuel"] = fuel.text

    except:
        pass

    try:

        trans = driver.find_element(By.XPATH, "//span[contains(text(),'Transmission')]/following::span[1]")

        specs["transmission"] = trans.text

    except:
        pass

    return specs


# ─────────────────────────────────────────────
# SCRAPE SINGLE LISTING
# ─────────────────────────────────────────────

def scrape_listing(driver, url):

    try:

        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        title = ""
        price_text = ""
        description = ""
        location_text = ""

        try:
            title = driver.find_element(By.TAG_NAME, "h1").text
        except:
            pass

        try:
            price_text = driver.find_element(
                By.XPATH,
                "//h3[contains(text(),'Rs')] | //span[contains(text(),'Rs')]"
            ).text
        except:
            pass

        try:
            location_text = driver.find_element(
                By.XPATH,
                "//span[contains(text(),',')]"
            ).text
        except:
            pass

        try:
            description = driver.find_element(
                By.XPATH,
                "//div[@aria-label='Description']"
            ).text

            description = description.replace("Description", "").strip()

        except:
            pass

        city = extract_city(location_text)

        price_pkr = convert_price(price_text)

        specs = extract_specs(driver)

        listing = {
            "title": title,
            "price_text": price_text,
            "price_pkr": price_pkr,
            "city": city,
            "year": specs["year"],
            "km_driven": specs["km_driven"],
            "fuel": specs["fuel"],
            "transmission": specs["transmission"],
            "description": description,
            "url": url
        }

        return listing

    except:

        print("Failed:", url)

        return None


# ─────────────────────────────────────────────
# MAIN SCRAPER
# ─────────────────────────────────────────────

def scrape_olx():

    driver = start_driver()

    all_listings = []

    for page in range(1, MAX_PAGES + 1):

        page_url = f"{BASE_URL}?page={page}"

        print("\nScraping page:", page)

        driver.get(page_url)

        time.sleep(4)

        links = get_listing_links(driver)

        for i, link in enumerate(links):

            print(f"Listing {i+1}/{len(links)}")

            listing = scrape_listing(driver, link)

            if listing:

                all_listings.append(listing)

        time.sleep(2)

    driver.quit()

    return all_listings


# ─────────────────────────────────────────────
# SAVE JSON
# ─────────────────────────────────────────────

def save_json(data):

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\nSaved listings:", len(data))


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":

    results = scrape_olx()

    save_json(results)

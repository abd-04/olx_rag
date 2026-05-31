import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))

from cleaner import build_embedding_text, clean_listing, extract_price_from_text


class CleanerTests(unittest.TestCase):
    def test_extracts_lakh_price(self):
        self.assertEqual(extract_price_from_text("Rs 27.5 Lakh"), 2750000)

    def test_extracts_crore_price(self):
        self.assertEqual(extract_price_from_text("1.2 crore"), 12000000)

    def test_preserves_bike_type_and_description_for_embeddings(self):
        listing = clean_listing({
            "title": "Honda CG 125",
            "price_text": "Rs 185,000",
            "city": "Johar Town, Lahore",
            "category": "bikes",
            "description": "Well maintained daily use bike",
            "url": "https://www.olx.com.pk/item/example",
            "Engine Capacity": "125 cc",
        })

        self.assertEqual(listing["vehicle_type"], "bike")
        self.assertEqual(listing["engine_cc"], "125 cc")
        self.assertIn("well maintained", build_embedding_text(listing))
        self.assertNotIn("car vehicle", build_embedding_text(listing))

    def test_rejects_listing_without_url(self):
        self.assertIsNone(clean_listing({"price_text": "Rs 500,000"}))

    def test_rejects_implausibly_low_car_price(self):
        self.assertIsNone(clean_listing({
            "title": "Honda Civic 2019",
            "price_text": "Rs.4,000",
            "price_pkr": 4000,
            "url": "https://www.olx.com.pk/item/example",
        }))


if __name__ == "__main__":
    unittest.main()

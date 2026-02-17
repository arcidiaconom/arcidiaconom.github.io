"""
Download World Bank "Population estimates and projections" data
for all 5-year age groups by gender for year 2050.

Indicators follow the pattern: SP.POP.<age_code>.<gender>
  e.g. SP.POP.3539.MA = Male population aged 35-39

Usage:
    python download_population_projections.py

Output:
    population_projections_2050.csv
"""

import csv
import time
import urllib.request
import json

# World Bank API v2 base URL
BASE_URL = "https://api.worldbank.org/v2"

# 5-year age group codes
AGE_GROUPS = [
    ("0004", "0-4"),
    ("0509", "5-9"),
    ("1014", "10-14"),
    ("1519", "15-19"),
    ("2024", "20-24"),
    ("2529", "25-29"),
    ("3034", "30-34"),
    ("3539", "35-39"),
    ("4044", "40-44"),
    ("4549", "45-49"),
    ("5054", "50-54"),
    ("5559", "55-59"),
    ("6064", "60-64"),
    ("6569", "65-69"),
    ("7074", "70-74"),
    ("7579", "75-79"),
    ("80UP", "80+"),
]

# Gender codes
GENDERS = [
    ("MA", "Male"),
    ("FE", "Female"),
]

YEAR = 2050
PER_PAGE = 500
OUTPUT_FILE = "population_projections_2050.csv"


def build_indicators():
    """Build the full list of indicator codes and their labels."""
    indicators = []
    for age_code, age_label in AGE_GROUPS:
        for gender_code, gender_label in GENDERS:
            indicator_id = f"SP.POP.{age_code}.{gender_code}"
            label = f"Population ages {age_label}, {gender_label.lower()}"
            indicators.append((indicator_id, age_label, gender_label))
    return indicators


def fetch_indicator(indicator_id, year):
    """Fetch all country data for one indicator and year from the World Bank API."""
    records = []
    page = 1

    while True:
        url = (
            f"{BASE_URL}/country/all/indicator/{indicator_id}"
            f"?date={year}&format=json&per_page={PER_PAGE}&page={page}"
        )
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  Error fetching {indicator_id} page {page}: {e}")
            break

        if not isinstance(data, list) or len(data) < 2 or data[1] is None:
            break

        metadata = data[0]
        entries = data[1]

        for entry in entries:
            country_code = entry.get("countryiso3code") or entry["country"]["id"]
            country_name = entry["country"]["value"]
            value = entry["value"]
            records.append({
                "country_code": country_code,
                "country_name": country_name,
                "value": value,
            })

        total_pages = metadata.get("pages", 1)
        if page >= total_pages:
            break
        page += 1

    return records


def main():
    indicators = build_indicators()
    print(f"Downloading {len(indicators)} indicators for year {YEAR}...")
    print(f"Age groups: {len(AGE_GROUPS)} | Genders: {len(GENDERS)}")
    print()

    all_rows = []

    for i, (indicator_id, age_label, gender_label) in enumerate(indicators, 1):
        print(f"[{i}/{len(indicators)}] Fetching {indicator_id} "
              f"(ages {age_label}, {gender_label})...")

        records = fetch_indicator(indicator_id, YEAR)
        print(f"  -> {len(records)} records")

        for rec in records:
            all_rows.append({
                "country_code": rec["country_code"],
                "country_name": rec["country_name"],
                "indicator": indicator_id,
                "age_group": age_label,
                "gender": gender_label,
                "year": YEAR,
                "value": rec["value"],
            })

        # Be polite to the API
        time.sleep(0.5)

    # Write CSV
    fieldnames = [
        "country_code", "country_name", "indicator",
        "age_group", "gender", "year", "value",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print()
    print(f"Done! Wrote {len(all_rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

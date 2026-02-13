"""Download World Bank Population Estimates and Projections data.

Indicators:
  - SP.POP.0004.FE  Female population aged 0-4
  - SP.POP.0004.MA  Male population aged 0-4
  - SP.POP.0509.FE  Female population aged 5-9

Country: World (WLD)
Years: 1990, 2050
Source: Population Estimates and Projections (source 40)
"""

import requests
import pandas as pd

BASE_URL = "https://api.worldbank.org/v2"
SOURCE = 40
COUNTRY = "WLD"
INDICATORS = ["SP.POP.0004.FE", "SP.POP.0004.MA", "SP.POP.0509.FE"]
YEARS = "1990;2050"


def fetch_indicator(indicator: str) -> list[dict]:
    """Fetch a single indicator from the World Bank API."""
    url = f"{BASE_URL}/country/{COUNTRY}/indicator/{indicator}"
    params = {
        "date": YEARS,
        "source": SOURCE,
        "format": "json",
        "per_page": 100,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if len(data) < 2 or data[1] is None:
        print(f"Warning: no data returned for {indicator}")
        return []

    return [
        {
            "indicator_id": row["indicator"]["id"],
            "indicator_name": row["indicator"]["value"],
            "country": row["country"]["value"],
            "year": int(row["date"]),
            "value": row["value"],
        }
        for row in data[1]
    ]


def main():
    rows = []
    for ind in INDICATORS:
        print(f"Fetching {ind}...")
        rows.extend(fetch_indicator(ind))

    df = pd.DataFrame(rows)
    print("\n" + df.to_string(index=False))

    output = "population_data.csv"
    df.to_csv(output, index=False)
    print(f"\nSaved to {output}")


if __name__ == "__main__":
    main()

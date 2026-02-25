#!/usr/bin/env python
"""
Download UN WPP2024 "Percentage of total population aged 0-14 years, both sexes"
for all countries, 1990-2100, using the UN Population Data Portal API.

Output: a tidy CSV with columns
    loc_id, iso3, location, year, pct_0_14

Usage:
    python scripts/download_wpp_data.py [data_output_dir]

Arguments (optional):
    data_output_dir   Folder where the CSV is saved.
                      Default: data/processed  (relative to working directory)

    Two-argument form also accepted for backward compatibility:
    python scripts/download_wpp_data.py [data_raw_dir] [data_output_dir]

Stata example — use the FULL Python path to avoid launcher issues on Windows:
    global PYTHON "C:/Users/.../AppData/Local/Programs/Python/Python313/python.exe"
    shell "${PYTHON}" "${root}/scripts/download_wpp_data.py" "${data_output}"
"""

import sys
import time
import requests
import pandas as pd
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL = "https://population.un.org/dataportalapi/api/v1"
YEAR_MIN = 1990
YEAR_MAX = 2100

# Accept 1-arg (output_dir) or 2-arg (raw_dir output_dir) for backward compat
if len(sys.argv) >= 3:
    PROCESSED_DIR = Path(sys.argv[2])
elif len(sys.argv) >= 2:
    PROCESSED_DIR = Path(sys.argv[1])
else:
    PROCESSED_DIR = Path("data/processed")

OUTPUT_FILE = PROCESSED_DIR / "wpp2024_pct_0_14_both_sexes.csv"

# ── API helpers ───────────────────────────────────────────────────────────────

def get_all_pages(url: str) -> list:
    """Walk paginated JSON responses; return combined list from the 'data' key."""
    rows, current = [], url
    while current:
        r = requests.get(current, timeout=120)
        r.raise_for_status()
        body = r.json()
        rows.extend(body.get("data", []))
        current = body.get("nextPage")
    return rows


def find_indicator() -> tuple:
    """
    Search Population-topic indicators for the 0-14 percentage series.
    Returns (indicator_id, indicator_name).
    """
    print("Querying indicator list (all topics) ...")
    inds = get_all_pages(f"{BASE_URL}/indicators?pageSize=500")
    print(f"  {len(inds)} indicators found")

    _AGE = {"0-14", "0\u201314", "0 to 14", "under 15", "under-15", "aged 0", "age 0"}
    _PCT = {"percent", "proportion", "share", "%", "pct"}

    for ind in inds:
        txt = " ".join([
            ind.get("Name", ""),
            ind.get("ShortName", ""),
            ind.get("DisplayName", ""),
        ]).lower()
        if any(a in txt for a in _AGE) and any(p in txt for p in _PCT):
            print(f"  Found: ID={ind['Id']}  \"{ind['Name']}\"")
            return ind["Id"], ind["Name"]

    # Not found — print ALL indicators so the user can pick the right one
    print("\n  No exact match. ALL available indicators:")
    for ind in inds:
        print(f"    ID {ind['Id']:4d}  {ind['Name']}")
    raise RuntimeError(
        "Could not auto-detect the 0-14 percentage indicator.\n"
        "Look at the list above, find the right ID, then replace find_indicator()\n"
        "with:  return <ID>, '<name>'"
    )


def get_country_ids() -> list:
    """Return location IDs for country-level entries (typeId == 4)."""
    print("Fetching country list ...")
    locs = get_all_pages(f"{BASE_URL}/locations?pageSize=500")
    countries = [loc for loc in locs if loc.get("typeId") == 4]
    print(f"  {len(countries)} countries found")
    return [loc["id"] for loc in countries]


def fetch_data(indicator_id: int, loc_ids: list) -> list:
    """Fetch indicator data for all locations in batches."""
    batch_size = 40
    n_batches = (len(loc_ids) + batch_size - 1) // batch_size
    print(f"Fetching data ({n_batches} batches of up to {batch_size} countries) ...")

    all_rows = []
    for i in range(0, len(loc_ids), batch_size):
        batch = loc_ids[i : i + batch_size]
        url = (
            f"{BASE_URL}/data/indicators/{indicator_id}"
            f"/locations/{','.join(map(str, batch))}"
            f"/start/{YEAR_MIN}/end/{YEAR_MAX}/?pageSize=5000"
        )
        rows = get_all_pages(url)
        all_rows.extend(rows)
        print(f"  Batch {i // batch_size + 1}/{n_batches}: {len(rows):,} rows")
        time.sleep(0.25)

    return all_rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1 – Discover indicator
    indicator_id, indicator_name = find_indicator()

    # 2 – Get country IDs
    loc_ids = get_country_ids()

    # 3 – Fetch data
    raw = fetch_data(indicator_id, loc_ids)
    if not raw:
        raise RuntimeError("API returned no rows. Check indicator ID and date range.")

    df = pd.DataFrame(raw)
    print(f"\nRaw response: {len(df):,} rows  |  columns: {list(df.columns)}")

    # 4 – Filter to both sexes + Estimates/Medium variant
    for col, keep in [
        ("sex",     {"both", "both sexes", "total", "b", "bt"}),
        ("variant", {"medium", "estimates", "est.", "median", "no variant"}),
    ]:
        if col in df.columns:
            before = len(df)
            df = df[df[col].astype(str).str.lower().str.strip().isin(keep)].copy()
            print(f"  {col} filter: {before:,} -> {len(df):,} rows")

    # 5 – Rename columns to tidy schema
    #     (column names vary across API versions; map whatever is present)
    rename = {}
    for src, dst in [
        ("locationId", "loc_id"), ("LocID",     "loc_id"),
        ("iso3Alpha",  "iso3"),   ("Iso3Alpha",  "iso3"),
        ("location",   "location"), ("Location", "location"),
        ("timeLabel",  "year"),   ("TimeLabel",  "year"), ("Time", "year"),
        ("value",      "pct_0_14"), ("Value",    "pct_0_14"),
    ]:
        if src in df.columns and dst not in df.columns:
            rename[src] = dst
    df = df.rename(columns=rename)

    keep_cols = [c for c in ["loc_id", "iso3", "location", "year", "pct_0_14"]
                 if c in df.columns]
    df = df[keep_cols]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    sort_key = ["loc_id", "year"] if "loc_id" in df.columns else ["location", "year"]
    df = df.sort_values(sort_key).reset_index(drop=True)

    # 6 – Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone.  {len(df):,} rows written -> {OUTPUT_FILE}")
    print(f"Columns: {list(df.columns)}")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()

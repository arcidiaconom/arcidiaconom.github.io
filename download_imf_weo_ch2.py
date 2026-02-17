"""
Download IMF World Economic Outlook (WEO) April 2025 — Chapter 2 Data
======================================================================

Chapter 2: "The Rise of the Silver Economy: Global Implications of Population Aging"

This script downloads:
  1. The WEO full database (tab-delimited) with all macro variables
  2. Chapter 2 figure data (Excel), PDF, and online annex
  3. Selected aging/demographic indicators via the IMF SDMX 3.0 API

Requirements:
    pip install requests pandas openpyxl

Usage:
    python download_imf_weo_ch2.py
"""

import os
import time
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = "imf_weo_apr2025"

# IMF file URLs
URLS = {
    # Full WEO database – tab-delimited, by country
    "WEOApr2025all.tsv": (
        "https://www.imf.org/-/media/Files/Publications/WEO/"
        "WEO-Database/2025/april/WEOApr2025all.ashx"
    ),
    # Full WEO database – tab-delimited, by country group
    "WEOApr2025alla.tsv": (
        "https://www.imf.org/-/media/Files/Publications/WEO/"
        "WEO-Database/2025/april/WEOApr2025alla.ashx"
    ),
    # Chapter 2 PDF
    "ch2.pdf": (
        "https://www.imf.org/-/media/Files/Publications/WEO/"
        "2025/April/English/ch2.ashx"
    ),
    # Chapter 2 online annex
    "ch2_online_annex.pdf": (
        "https://www.imf.org/-/media/Files/Publications/WEO/"
        "2025/April/English/ch2onlineannex.ashx"
    ),
}

# Candidate URLs for Chapter 2 underlying figure data (Excel).
# The IMF does not always use the same naming convention, so we try several.
CH2_FIGURE_DATA_CANDIDATES = [
    ("https://www.imf.org/-/media/Files/Publications/WEO/"
     "2025/April/English/ch2figuredata.xlsx"),
    ("https://www.imf.org/-/media/Files/Publications/WEO/"
     "2025/April/English/chapter2figuredata.xlsx"),
    ("https://www.imf.org/-/media/Files/Publications/WEO/"
     "2025/April/English/Ch2Data.xlsx"),
    ("https://www.imf.org/-/media/Files/Publications/WEO/"
     "2025/April/English/ch2-figure-data.xlsx"),
]

# IMF SDMX 3.0 API – base URL
SDMX_BASE = "https://api.imf.org/external/sdmx/3.0"

# WEO indicators relevant to Chapter 2 (aging, demographics, labor, fiscal)
# Full list: https://www.imf.org/en/publications/weo/weo-database/2025/april
AGING_INDICATORS = [
    "LP",        # Population (persons)
    "LUR",       # Unemployment rate
    "LE",        # Employment
    "NGDP_RPCH", # Real GDP growth
    "GGR_NGDP",  # General government revenue (% of GDP)
    "GGX_NGDP",  # General government total expenditure (% of GDP)
    "GGXCNL_NGDP",  # General government net lending/borrowing (% of GDP)
    "BCA_NGDPD",    # Current account balance (% of GDP)
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def download_file(url: str, dest: str, retries: int = 3) -> bool:
    """Download a file with retry logic. Returns True on success."""
    for attempt in range(retries):
        try:
            print(f"  Downloading {url} ...")
            resp = requests.get(url, timeout=120, allow_redirects=True)
            if resp.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                size_mb = len(resp.content) / (1024 * 1024)
                print(f"  -> Saved to {dest} ({size_mb:.1f} MB)")
                return True
            else:
                print(f"  -> HTTP {resp.status_code}")
        except requests.RequestException as exc:
            print(f"  -> Error: {exc}")
        if attempt < retries - 1:
            wait = 2 ** (attempt + 1)
            print(f"  Retrying in {wait}s ...")
            time.sleep(wait)
    return False


# ---------------------------------------------------------------------------
# 1. Download WEO database & Chapter 2 documents
# ---------------------------------------------------------------------------

def download_core_files() -> None:
    """Download the WEO database and Chapter 2 documents."""
    print("\n=== Downloading WEO database & Chapter 2 documents ===\n")
    for filename, url in URLS.items():
        dest = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(dest):
            print(f"  {filename} already exists, skipping.")
            continue
        ok = download_file(url, dest)
        if not ok:
            print(f"  WARNING: Could not download {filename}")
    print()


# ---------------------------------------------------------------------------
# 2. Try to download Chapter 2 figure data (Excel)
# ---------------------------------------------------------------------------

def download_ch2_figure_data() -> None:
    """Try candidate URLs for the Chapter 2 underlying figure data."""
    print("=== Attempting to download Chapter 2 figure data (Excel) ===\n")
    dest = os.path.join(OUTPUT_DIR, "ch2_figure_data.xlsx")
    if os.path.exists(dest):
        print(f"  {dest} already exists, skipping.\n")
        return
    for url in CH2_FIGURE_DATA_CANDIDATES:
        ok = download_file(url, dest, retries=1)
        if ok:
            return
    print(
        "  NOTE: Could not find Chapter 2 figure data Excel file.\n"
        "  The IMF may not publish a separate file, or the URL may differ.\n"
        "  You can check the publication page manually:\n"
        "  https://www.imf.org/en/publications/weo/issues/2025/04/22/"
        "world-economic-outlook-april-2025\n"
    )


# ---------------------------------------------------------------------------
# 3. Load and filter the WEO database for aging-related indicators
# ---------------------------------------------------------------------------

def load_weo_database() -> pd.DataFrame | None:
    """Load the tab-delimited WEO database and return a DataFrame."""
    path = os.path.join(OUTPUT_DIR, "WEOApr2025all.tsv")
    if not os.path.exists(path):
        print("  WEO database file not found. Skipping.\n")
        return None

    print(f"  Reading {path} ...")
    # The IMF file uses tab separators and has some encoding quirks
    df = pd.read_csv(path, sep="\t", encoding="latin-1", low_memory=False)
    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns.\n")
    return df


def filter_aging_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the WEO database for indicators relevant to Chapter 2."""
    mask = df["WEO Subject Code"].isin(AGING_INDICATORS)
    filtered = df.loc[mask].copy()
    print(f"  Filtered to {len(filtered):,} rows for indicators: "
          f"{', '.join(AGING_INDICATORS)}\n")
    return filtered


# ---------------------------------------------------------------------------
# 4. Query IMF SDMX 3.0 API for WEO data
# ---------------------------------------------------------------------------

def query_sdmx_weo(
    countries: list[str] | None = None,
    indicator: str = "NGDP_RPCH",
) -> pd.DataFrame | None:
    """
    Query the IMF SDMX 3.0 API for WEO data.

    Parameters
    ----------
    countries : list of ISO country codes, e.g. ["USA", "DEU", "JPN"].
                If None, fetches all countries.
    indicator : WEO subject code, e.g. "NGDP_RPCH" (real GDP growth).

    Returns
    -------
    DataFrame or None on failure.
    """
    country_key = "+".join(countries) if countries else ""
    # SDMX 3.0 data query: /data/dataflow/{agency}/{dataflow}/{version}/{key}
    url = (
        f"{SDMX_BASE}/data/dataflow/IMF.RES/WEO/latest/"
        f"{country_key}.{indicator}.A"
        f"?format=csv"
    )
    print(f"  Querying SDMX API: {url}")
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(resp.text))
            print(f"  -> Received {len(df):,} rows.\n")
            return df
        else:
            print(f"  -> HTTP {resp.status_code}: {resp.text[:200]}\n")
    except requests.RequestException as exc:
        print(f"  -> Error: {exc}\n")
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ensure_dir(OUTPUT_DIR)

    # Step 1 – Download WEO database + Chapter 2 docs
    download_core_files()

    # Step 2 – Try to get Chapter 2 figure data Excel
    download_ch2_figure_data()

    # Step 3 – Load and filter the WEO database
    print("=== Loading WEO database & filtering aging-related indicators ===\n")
    df = load_weo_database()
    if df is not None:
        filtered = filter_aging_indicators(df)
        out_path = os.path.join(OUTPUT_DIR, "weo_aging_indicators.csv")
        filtered.to_csv(out_path, index=False)
        print(f"  Saved filtered data to {out_path}\n")

        # Show a quick summary
        print("  Available indicators in filtered data:")
        for code, name in (
            filtered.groupby("WEO Subject Code")["Subject Descriptor"]
            .first()
            .items()
        ):
            count = (filtered["WEO Subject Code"] == code).sum()
            print(f"    {code:20s} {name:50s} ({count} rows)")
        print()

    # Step 4 – Query SDMX API for a sample (real GDP growth, G7 countries)
    print("=== Querying IMF SDMX 3.0 API (sample: Real GDP growth, G7) ===\n")
    g7 = ["USA", "GBR", "FRA", "DEU", "ITA", "JPN", "CAN"]
    sdmx_df = query_sdmx_weo(countries=g7, indicator="NGDP_RPCH")
    if sdmx_df is not None:
        out_path = os.path.join(OUTPUT_DIR, "sdmx_gdp_growth_g7.csv")
        sdmx_df.to_csv(out_path, index=False)
        print(f"  Saved SDMX data to {out_path}\n")

    # Summary
    print("=" * 60)
    print("Done. Files saved in:", os.path.abspath(OUTPUT_DIR))
    print()
    print("Key files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(fpath) / (1024 * 1024)
        print(f"  {f:40s} {size:8.2f} MB")
    print()
    print("For more information on the WEO database:")
    print("  https://www.imf.org/en/publications/weo/weo-database/2025/april")
    print()
    print("Chapter 2 publication page:")
    print("  https://www.imf.org/en/publications/weo/issues/2025/04/22/"
          "world-economic-outlook-april-2025")


if __name__ == "__main__":
    main()

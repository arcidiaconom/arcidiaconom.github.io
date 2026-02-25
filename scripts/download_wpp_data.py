#!/usr/bin/env python
"""
Download UN WPP2024 "Percentage of total population aged 0-14 years, both sexes"
for all countries, 1990-2100, from the WPP2024 bulk CSV files (no login required).

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
import io
import requests
import pandas as pd
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

YEAR_MIN = 1990
YEAR_MAX = 2100

# WPP2024 bulk CSV files (no authentication required)
WPP_BASE = (
    "https://population.un.org/wpp/Download/Files/"
    "1_Indicators%20(Standard)/CSV_FILES"
)
CSV_FILES = [
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Estimates.csv",
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Medium.csv",
]

# Accept 1-arg (output_dir) or 2-arg (raw_dir output_dir) for backward compat
if len(sys.argv) >= 3:
    PROCESSED_DIR = Path(sys.argv[2])
elif len(sys.argv) >= 2:
    PROCESSED_DIR = Path(sys.argv[1])
else:
    PROCESSED_DIR = Path("data/processed")

OUTPUT_FILE = PROCESSED_DIR / "wpp2024_pct_0_14_both_sexes.csv"

# ── Download helpers ───────────────────────────────────────────────────────────

def download_csv(url: str) -> pd.DataFrame:
    print(f"  Downloading {url.split('/')[-1]} ...")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1 – Download and stack estimates + medium projections
    print("Downloading WPP2024 bulk CSV files ...")
    frames = []
    for url in CSV_FILES:
        df = download_csv(url)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    print(f"  Combined: {len(df):,} rows  |  columns: {list(df.columns)}")

    # 2 – Keep countries only (LocTypeID == 4)
    if "LocTypeID" in df.columns:
        before = len(df)
        df = df[df["LocTypeID"] == 4].copy()
        print(f"  Country filter (LocTypeID==4): {before:,} -> {len(df):,} rows")
    else:
        # Fallback: filter by 3-letter ISO code presence
        iso_col = next((c for c in df.columns if "iso3" in c.lower()), None)
        if iso_col:
            before = len(df)
            df = df[df[iso_col].astype(str).str.len() == 3].copy()
            print(f"  Country filter (iso3 length): {before:,} -> {len(df):,} rows")
        else:
            print("  WARNING: could not filter to countries only")

    # 3 – Year range
    time_col = next((c for c in df.columns if c.lower() in ("time", "year")), None)
    if time_col:
        df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
        before = len(df)
        df = df[(df[time_col] >= YEAR_MIN) & (df[time_col] <= YEAR_MAX)].copy()
        print(f"  Year filter {YEAR_MIN}-{YEAR_MAX}: {before:,} -> {len(df):,} rows")

    # 4 – Find the 0-14 percentage column
    #     WPP2024 names it "PopAge0_14" in the percentage file, but let's be safe
    age_col = next(
        (c for c in df.columns
         if ("0_14" in c or "0-14" in c or "014" in c.lower())
         and ("pct" in c.lower() or "pop" in c.lower() or "age" in c.lower())),
        None,
    )
    if age_col is None:
        # Last resort: show all columns and raise
        raise RuntimeError(
            f"Cannot find 0-14 age column. Available columns:\n{list(df.columns)}"
        )
    print(f"  Using 0-14 column: '{age_col}'")

    # 5 – Build tidy output
    rename = {}
    for src, dst in [
        ("LocID",      "loc_id"),
        ("ISO3_code",  "iso3"),
        ("Location",   "location"),
        (time_col,     "year"),
        (age_col,      "pct_0_14"),
    ]:
        if src and src in df.columns:
            rename[src] = dst
    df = df.rename(columns=rename)

    keep_cols = [c for c in ["loc_id", "iso3", "location", "year", "pct_0_14"]
                 if c in df.columns]
    df = df[keep_cols].copy()
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

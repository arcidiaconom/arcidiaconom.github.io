#!/usr/bin/env python3
"""
Download and process UN WPP2024:
  "Population Percentage by Select Age Groups - Both Sexes (XLSX)"
  Standard Projections > Population

Outputs a clean CSV with population share columns for 4 age groups,
all countries, years 1990-2100.

Usage:
    python scripts/download_wpp_data.py
"""

import sys
import requests
import pandas as pd
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

# Direct download URL for WPP2024 Standard Projections > Population >
# "Population Percentage by Select Age Groups - Both Sexes"
FILE_URL = (
    "https://population.un.org/wpp/assets/Files/"
    "WPP2024_POP_F05_3_PERCENTAGE_OF_POPULATION_BY_SELECT_AGE_GROUP_BOTH_SEXES.xlsx"
)

RAW_DIR       = Path.home() / "Downloads"
PROCESSED_DIR = Path("data/processed")

RAW_FILE      = RAW_DIR / "WPP2024_pct_age_groups_both_sexes.xlsx"
OUTPUT_FILE   = PROCESSED_DIR / "wpp2024_pct_age_groups_both_sexes.csv"

YEAR_MIN = 1990
YEAR_MAX = 2100

# Variant to keep (Standard Projections uses "Medium" for projections)
# Set to None to keep all variants.
KEEP_VARIANT = "Medium"

# ── Download ─────────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path) -> None:
    """Stream-download url → dest, with a simple progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading:\n  {url}")
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(
            f"\nHTTP error {e.response.status_code}. "
            "The URL may have changed – please check:\n"
            "  https://population.un.org/wpp/downloads"
            "?folder=Standard%20Projections&group=Population\n"
            "and update FILE_URL at the top of this script.",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.ConnectionError as e:
        print(f"\nConnection error: {e}", file=sys.stderr)
        sys.exit(1)

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=65_536):
            fh.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {pct:5.1f}%  ({downloaded:,} / {total:,} bytes)", end="", flush=True)
    print(f"\nSaved → {dest}")


# ── Parse XLSX ───────────────────────────────────────────────────────────────

def detect_header_row(path: Path, sheet: str, search_limit: int = 25) -> int:
    """
    WPP XLSX files embed several rows of notes before the real column headers.
    Scan up to `search_limit` rows for the row that contains 'LocID' or 'Location'.
    Falls back to row 16 (0-indexed) which is the historical default.
    """
    peek = pd.read_excel(path, sheet_name=sheet, nrows=search_limit, header=None)
    for i, row in peek.iterrows():
        values_lower = {str(v).strip().lower() for v in row}
        if values_lower & {"locid", "location", "iso3 alpha-code"}:
            return i
    return 16  # safe fallback


def load_xlsx(path: Path) -> pd.DataFrame:
    print(f"Reading XLSX from {path} …")
    xl = pd.ExcelFile(path, engine="openpyxl")
    sheet = xl.sheet_names[0]
    header_row = detect_header_row(path, sheet)
    print(f"  Header detected at row {header_row} (sheet '{sheet}')")
    df = pd.read_excel(path, sheet_name=sheet, header=header_row, engine="openpyxl")
    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]
    print(f"  Loaded {len(df):,} rows × {len(df.columns)} columns")
    return df


# ── Process ───────────────────────────────────────────────────────────────────

# Column-name aliases that appear across WPP editions
_YEAR_ALIASES     = {"year", "time"}
_LOCID_ALIASES    = {"locid", "loc_id", "locationid"}
_LOCNAME_ALIASES  = {"location", "region, subregion, country or area *",
                     "region, subregion, country or area"}
_ISO3_ALIASES     = {"iso3 alpha-code", "iso3_alpha_code", "iso3alpha", "iso3"}
_TYPE_ALIASES     = {"loctypename", "loctype", "type", "loctypeid"}
_VARIANT_ALIASES  = {"variant", "varid"}


def _find_col(df: pd.DataFrame, aliases: set) -> str | None:
    for c in df.columns:
        if c.lower().strip() in aliases:
            return c
    return None


def _age_group_cols(df: pd.DataFrame) -> list[str]:
    """
    Identify the percentage-by-age-group columns.
    They are the numeric columns that come after the metadata columns.
    WPP typically names them as age ranges or descriptive labels like
    '0-4', '5-14', '15-24', '25-64', '65+', '80+', etc.
    """
    meta_keywords = {
        "sort", "locid", "notes", "iso", "sdmx", "type", "parent",
        "location", "region", "varid", "variant", "time", "year",
        "unnamed", "nan",
    }
    age_cols = []
    for c in df.columns:
        c_lower = c.lower().strip()
        if any(kw in c_lower for kw in meta_keywords):
            continue
        # Accept columns that look like age ranges or "under X" / "X+" labels
        age_cols.append(c)
    return age_cols


def process(df: pd.DataFrame) -> pd.DataFrame:
    # ── Locate key columns ──────────────────────────────────────────────────
    year_col    = _find_col(df, _YEAR_ALIASES)
    locid_col   = _find_col(df, _LOCID_ALIASES)
    locname_col = _find_col(df, _LOCNAME_ALIASES)
    iso3_col    = _find_col(df, _ISO3_ALIASES)
    type_col    = _find_col(df, _TYPE_ALIASES)
    variant_col = _find_col(df, _VARIANT_ALIASES)

    if year_col is None:
        raise RuntimeError(
            "Could not find a Year/Time column. "
            f"Available columns: {list(df.columns)}"
        )

    print(f"  Year column  : '{year_col}'")
    print(f"  Location col : '{locname_col}'")
    print(f"  LocID col    : '{locid_col}'")
    print(f"  ISO3 col     : '{iso3_col}'")
    print(f"  Type col     : '{type_col}'")
    print(f"  Variant col  : '{variant_col}'")

    # ── Filter variant ──────────────────────────────────────────────────────
    if KEEP_VARIANT and variant_col:
        before = len(df)
        df = df[df[variant_col].astype(str).str.strip().str.lower()
                == KEEP_VARIANT.lower()].copy()
        print(f"  Variant filter '{KEEP_VARIANT}': {before:,} → {len(df):,} rows")

    # ── Filter years ────────────────────────────────────────────────────────
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df[df[year_col].between(YEAR_MIN, YEAR_MAX)].copy()
    print(f"  Year filter {YEAR_MIN}–{YEAR_MAX}: {len(df):,} rows remain")

    # ── Filter to countries only ────────────────────────────────────────────
    if type_col:
        mask = df[type_col].astype(str).str.lower().str.contains("country", na=False)
        df = df[mask].copy()
        print(f"  Country-only filter: {len(df):,} rows remain")
    else:
        print("  WARNING: no Type column found – keeping all location types.")

    # ── Identify the 4 age-group percentage columns ────────────────────────
    age_cols = _age_group_cols(df)
    print(f"\n  Age-group columns found ({len(age_cols)}):")
    for c in age_cols:
        print(f"    • {c}")

    if len(age_cols) == 0:
        raise RuntimeError("No age-group columns detected – check column names.")

    # ── Build tidy output ───────────────────────────────────────────────────
    keep_meta = [c for c in [locid_col, iso3_col, locname_col, year_col] if c]
    df_out = df[keep_meta + age_cols].copy()

    # Rename meta columns to standard names
    rename = {}
    if locid_col:   rename[locid_col]   = "loc_id"
    if iso3_col:    rename[iso3_col]    = "iso3"
    if locname_col: rename[locname_col] = "location"
    if year_col:    rename[year_col]    = "year"
    df_out = df_out.rename(columns=rename)

    df_out["year"] = df_out["year"].astype(int)
    df_out = df_out.sort_values(["loc_id", "year"] if "loc_id" in df_out.columns
                                else ["location", "year"]).reset_index(drop=True)

    return df_out


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1 – download (skip if already cached)
    if RAW_FILE.exists():
        print(f"Raw file already cached: {RAW_FILE}")
    else:
        download_file(FILE_URL, RAW_FILE)

    # Step 2 – load
    df = load_xlsx(RAW_FILE)

    # Step 3 – process
    print("\nProcessing …")
    df_out = process(df)

    # Step 4 – save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone.  {len(df_out):,} rows written → {OUTPUT_FILE}")
    print(f"Columns: {list(df_out.columns)}")


if __name__ == "__main__":
    main()

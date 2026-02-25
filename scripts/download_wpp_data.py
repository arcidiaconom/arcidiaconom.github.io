#!/usr/bin/env python
"""
Download UN WPP2024 "Percentage of total population aged 0-14 years, both sexes"
for all countries, 1990-2100, from the WPP2024 bulk CSV files (no login required).

Strategy:
  1. Try the dedicated "percentage by broad age group" CSV files.
  2. If those 404, fall back to the 5-year age-group population files and
     compute the 0-14 share from them.

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
import gzip
import requests
import pandas as pd
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

YEAR_MIN = 1990
YEAR_MAX = 2100

WPP_BASE = (
    "https://population.un.org/wpp/Download/Files/"
    "1_Indicator%20(Standard)/CSV_FILES"
)

# Candidate percentage files (tried in order; first 200 wins)
PCT_CANDIDATES = [
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Estimates.csv.gz",
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Medium.csv.gz",
    f"{WPP_BASE}/WPP2024_PercentageByBroadAgeSex_Estimates.csv.gz",
    f"{WPP_BASE}/WPP2024_PercentageByBroadAgeSex_Medium.csv.gz",
    f"{WPP_BASE}/WPP2024_PopByBroadAgeSex_Estimates.csv.gz",
    f"{WPP_BASE}/WPP2024_PopByBroadAgeSex_Medium.csv.gz",
    # plain CSV variants (no compression)
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Estimates.csv",
    f"{WPP_BASE}/WPP2024_PctByBroadAgeSex_Medium.csv",
    f"{WPP_BASE}/WPP2024_PopByBroadAgeSex_Estimates.csv",
    f"{WPP_BASE}/WPP2024_PopByBroadAgeSex_Medium.csv",
]

# Fallback: 5-year age-group population files (compute 0-14 share manually)
POP5_CANDIDATES = [
    f"{WPP_BASE}/WPP2024_Population1JanuaryByAge5GroupSex_Estimates.csv.gz",
    f"{WPP_BASE}/WPP2024_Population1JanuaryByAge5GroupSex_Medium.csv.gz",
    f"{WPP_BASE}/WPP2024_PopulationByAge5GroupSex_Estimates.csv.gz",
    f"{WPP_BASE}/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz",
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

def try_download(url: str) -> pd.DataFrame | None:
    """Return a DataFrame if the URL exists (200), else None."""
    fname = url.split("/")[-1]
    try:
        r = requests.get(url, timeout=300)
        if r.status_code == 404:
            print(f"    404 {fname}")
            return None
        r.raise_for_status()
    except requests.HTTPError as e:
        print(f"    HTTP error {e} for {fname}")
        return None

    print(f"    OK  {fname} ({len(r.content):,} bytes)")
    content = r.content
    if url.endswith(".gz"):
        content = gzip.decompress(content)
    return pd.read_csv(io.BytesIO(content))


def download_first(candidates: list[str]) -> pd.DataFrame | None:
    """Try each URL in order; return the first that succeeds."""
    for url in candidates:
        df = try_download(url)
        if df is not None:
            return df
    return None


# ── Processing helpers ─────────────────────────────────────────────────────────

def filter_countries_years(df: pd.DataFrame) -> pd.DataFrame:
    """Keep countries (LocTypeID==4 or 3-char ISO) within YEAR_MIN..YEAR_MAX."""
    if "LocTypeID" in df.columns:
        df = df[df["LocTypeID"] == 4].copy()
    else:
        iso_col = next((c for c in df.columns if "iso3" in c.lower()), None)
        if iso_col:
            df = df[df[iso_col].astype(str).str.len() == 3].copy()

    time_col = next((c for c in df.columns if c.lower() in ("time", "year")), None)
    if time_col:
        df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
        df = df[(df[time_col] >= YEAR_MIN) & (df[time_col] <= YEAR_MAX)].copy()
    return df


def build_tidy(df: pd.DataFrame, pct_col: str) -> pd.DataFrame:
    """Rename to standard schema and keep only needed columns."""
    time_col = next((c for c in df.columns if c.lower() in ("time", "year")), None)
    rename = {}
    for src, dst in [
        ("LocID",     "loc_id"),
        ("ISO3_code", "iso3"),
        ("Location",  "location"),
        (time_col,    "year"),
        (pct_col,     "pct_0_14"),
    ]:
        if src and src in df.columns:
            rename[src] = dst
    df = df.rename(columns=rename)
    keep = [c for c in ["loc_id", "iso3", "location", "year", "pct_0_14"] if c in df.columns]
    df = df[keep].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    sort_key = ["loc_id", "year"] if "loc_id" in df.columns else ["location", "year"]
    return df.sort_values(sort_key).reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── Path A: dedicated percentage files ────────────────────────────────────
    print("Trying percentage-by-broad-age-group files ...")
    pct_frames = []
    for url in PCT_CANDIDATES:
        df = try_download(url)
        if df is not None:
            pct_frames.append(df)

    if pct_frames:
        df = pd.concat(pct_frames, ignore_index=True)
        print(f"  Combined pct rows: {len(df):,}  columns: {list(df.columns)}")
        df = filter_countries_years(df)

        # Find the 0-14 column
        age_col = next(
            (c for c in df.columns
             if ("0_14" in c or "0-14" in c)
             and any(k in c.lower() for k in ("pct", "pop", "perc", "age"))),
            None,
        )
        if age_col:
            print(f"  Using 0-14 column: '{age_col}'")
            df = build_tidy(df, age_col)
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"\nDone.  {len(df):,} rows written -> {OUTPUT_FILE}")
            print(f"Columns: {list(df.columns)}")
            print(df.head(10).to_string())
            return
        print(f"  WARNING: no 0-14 column found in pct files. Columns: {list(df.columns)}")

    # ── Path B: 5-year age-group population (compute percentage) ──────────────
    print("\nFalling back to 5-year age-group population files ...")
    pop_frames = []
    for url in POP5_CANDIDATES:
        df = try_download(url)
        if df is not None:
            pop_frames.append(df)

    if not pop_frames:
        raise RuntimeError(
            "All download attempts failed.\n"
            "Please check the WPP2024 downloads page for the correct filenames:\n"
            "  https://population.un.org/wpp/downloads"
        )

    df = pd.concat(pop_frames, ignore_index=True)
    print(f"  Combined pop5 rows: {len(df):,}  columns: {list(df.columns)}")
    df = filter_countries_years(df)

    # Identify columns
    time_col  = next((c for c in df.columns if c.lower() in ("time", "year")), None)
    age_col   = next((c for c in df.columns if "agegrp" in c.lower() or "agestart" in c.lower() or c.lower() in ("agegrp", "agestart", "age_grp")), None)
    total_col = next((c for c in df.columns if "poptotal" in c.lower() or c.lower() in ("poptotal", "pop_total", "total")), None)

    if not all([time_col, age_col, total_col]):
        raise RuntimeError(
            f"Cannot identify required columns in 5yr file.\nColumns: {list(df.columns)}"
        )
    print(f"  time='{time_col}', age='{age_col}', pop='{total_col}'")

    df[total_col] = pd.to_numeric(df[total_col], errors="coerce")
    df[time_col]  = pd.to_numeric(df[time_col],  errors="coerce")

    # Age group column may be string ("0-4") or numeric start (0, 5, 10 …)
    age_vals = df[age_col].astype(str).str.strip()
    is_0_14 = age_vals.isin(["0-4", "5-9", "10-14", "0", "5", "10"])

    loc_col = next((c for c in df.columns if c in ("LocID", "locId", "loc_id")), None)
    group_cols = [c for c in [loc_col, time_col] if c]

    pop_0_14 = (
        df[is_0_14]
        .groupby(group_cols)[total_col].sum()
        .reset_index()
        .rename(columns={total_col: "pop_0_14"})
    )
    pop_total = (
        df.groupby(group_cols)[total_col].sum()
        .reset_index()
        .rename(columns={total_col: "pop_total"})
    )
    merged = pop_0_14.merge(pop_total, on=group_cols)
    merged["pct_0_14"] = (merged["pop_0_14"] / merged["pop_total"] * 100).round(2)

    # Attach location metadata
    meta_cols = [c for c in ["LocID", "ISO3_code", "Location"] if c in df.columns]
    meta = df[group_cols + meta_cols].drop_duplicates()
    merged = merged.merge(meta, on=group_cols, how="left")

    df_out = build_tidy(merged, "pct_0_14")
    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone.  {len(df_out):,} rows written -> {OUTPUT_FILE}")
    print(f"Columns: {list(df_out.columns)}")
    print(df_out.head(10).to_string())


if __name__ == "__main__":
    main()

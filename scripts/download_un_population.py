#!/usr/bin/env python3
"""
UN World Population Prospects Data Download Script (Python Version)
===================================================================

This script downloads total population data from the UN World Population
Prospects 2024 bulk CSV file.

Data specifications:
- Location: All individual countries (~240 locations)
- Scenario: Medium variant only
- Sex: Both genders combined
- Time period: 1960-2050
- Output: CSV file with country names, location IDs, years, and population

Required packages: pandas, requests
Installation: pip install pandas requests

Usage: python download_un_population.py
"""

import os
import zipfile
import pandas as pd
import requests
from pathlib import Path

# Configuration
DATA_URL = "https://population.un.org/wpp/Download/Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_TotalPopulationBySex.zip"
ZIP_FILE = "WPP2024_TotalPopulationBySex.zip"
CSV_FILE = "WPP2024_TotalPopulationBySex.csv"
OUTPUT_FILE = "un_population_all_countries_1960_2050.csv"
START_YEAR = 1960
END_YEAR = 2050

print("=" * 60)
print("UN Population Data Download - Direct CSV Method (Python)")
print("Source: WPP2024 Bulk CSV File")
print("=" * 60)
print()

# =============================================================================
# STEP 1: DOWNLOAD OR LOCATE DATA FILE
# =============================================================================

print("Step 1: Locating data file...")

if os.path.exists(CSV_FILE):
    file_size_mb = os.path.getsize(CSV_FILE) / (1024 ** 2)
    print(f"  ✓ Found existing file: {CSV_FILE}")
    print(f"  File size: {file_size_mb:.1f} MB\n")
else:
    print(f"  File not found locally, attempting download...")
    print(f"  URL: {DATA_URL}")

    # Try to download the ZIP file
    try:
        response = requests.get(DATA_URL, stream=True, timeout=30)
        response.raise_for_status()

        # Save the ZIP file
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0

        with open(ZIP_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r  Downloading: {progress:.1f}%", end="", flush=True)

        print(f"\n  ✓ Download complete: {ZIP_FILE} ({os.path.getsize(ZIP_FILE) / (1024 ** 2):.1f} MB)")

        # Extract the CSV file
        print("  Extracting CSV file...")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall(".")

        if os.path.exists(CSV_FILE):
            print(f"  ✓ Extracted: {CSV_FILE}\n")
            # Clean up ZIP file
            os.remove(ZIP_FILE)
        else:
            raise Exception("Failed to extract CSV file from ZIP archive")

    except requests.exceptions.RequestException as e:
        print(f"\n  ✗ Download failed: {e}\n")
        print("=" * 60)
        print("MANUAL DOWNLOAD REQUIRED")
        print("=" * 60)
        print("\nThe automatic download failed (likely due to network restrictions).")
        print("Please download the file manually:\n")
        print("1. Go to: https://population.un.org/wpp/downloads")
        print("2. Navigate to: Standard Projections > CSV format")
        print("3. Download: WPP2024_TotalPopulationBySex.zip")
        print("4. Extract the CSV file to this directory")
        print("5. Run this script again\n")
        print("Or download directly:")
        print(f"   {DATA_URL}\n")
        exit(1)
    except Exception as e:
        print(f"\n  ✗ Error: {e}\n")
        exit(1)

# =============================================================================
# STEP 2: READ AND FILTER DATA
# =============================================================================

print("Step 2: Reading and filtering data...")
print("  This may take a moment (file contains ~50k rows)...")

# Read the full CSV file
raw_data = pd.read_csv(CSV_FILE)

print(f"  Loaded: {len(raw_data):,} rows, {len(raw_data.columns)} columns")

# Show column names
print("\n  Column names:")
print(f"    {', '.join(raw_data.columns)}\n")

# Filter the data:
# - Variant = Medium
# - Year range: 1960-2050
# - Both sexes combined (if Sex column exists)
# - Exclude regional aggregates (keep only countries with ISO3 codes)
# - Location ID < 900 (individual countries) or = 900 (World)

print("  Filtering data...")

# Build filter conditions
filters = (
    # Medium variant
    (raw_data['Variant'].str.contains('Medium', case=False, na=False)) &
    # Year range
    (raw_data['Time'] >= START_YEAR) &
    (raw_data['Time'] <= END_YEAR) &
    # Only countries with ISO3 codes
    (raw_data['ISO3_code'].notna()) &
    (raw_data['ISO3_code'] != '') &
    (raw_data['ISO3_code'].str.len() == 3) &
    # Location ID range
    ((raw_data['LocID'] < 900) | (raw_data['LocID'] == 900))
)

# Apply filters
filtered_data = raw_data[filters].copy()

# Select and rename columns
clean_data = filtered_data[['Location', 'LocID', 'Time', 'PopTotal']].copy()
clean_data.columns = ['Country', 'LocationId', 'Year', 'Population']

# Convert data types
clean_data['Year'] = clean_data['Year'].astype(int)
clean_data['LocationId'] = clean_data['LocationId'].astype(int)
clean_data['Population'] = clean_data['Population'].astype(float) * 1000  # Convert from thousands

# Sort and remove duplicates
clean_data = clean_data.sort_values(['Country', 'Year']).drop_duplicates()

print(f"  Processed: {len(clean_data):,} rows")
print(f"  Countries: {clean_data['Country'].nunique()}")
print(f"  Year range: {clean_data['Year'].min()}-{clean_data['Year'].max()}\n")

# =============================================================================
# STEP 3: EXPORT TO CSV
# =============================================================================

print("Step 3: Exporting to CSV...")
clean_data.to_csv(OUTPUT_FILE, index=False)

file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
print(f"  ✓ File created: {OUTPUT_FILE} ({file_size_kb:.1f} KB)")

# =============================================================================
# VALIDATION & SUMMARY
# =============================================================================

print("\n" + "=" * 60)
print("COMPLETE!")
print("=" * 60)
print(f"Countries: {clean_data['Country'].nunique()} | Rows: {len(clean_data):,}")
print(f"Year range: {clean_data['Year'].min()}-{clean_data['Year'].max()} | File: {OUTPUT_FILE}")

print("\nFirst 15 rows:")
print(clean_data.head(15).to_string(index=False))

# Additional validation
duplicates = clean_data.groupby(['Country', 'Year']).size()
duplicates = duplicates[duplicates > 1]

if len(duplicates) > 0:
    print(f"\n⚠ WARNING: Found {len(duplicates)} duplicate Country-Year combinations")
else:
    print("\n✓ No duplicate Country-Year combinations")

negative_pop = (clean_data['Population'] < 0).sum()
if negative_pop > 0:
    print(f"⚠ WARNING: Found {negative_pop} negative population values")
else:
    print("✓ All population values are positive")

missing_pop = clean_data['Population'].isna().sum()
if missing_pop > 0:
    print(f"⚠ WARNING: Found {missing_pop} missing population values")
else:
    print("✓ No missing population values")

print("\n" + "=" * 60)
print("Done! Use this file for your visualizations.")
print("=" * 60)

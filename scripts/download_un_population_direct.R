#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Download Script (Direct Download Version)
# ============================================================================
#
# This script downloads total population data from the UN World Population
# Prospects 2024 bulk CSV file (not the API).
#
# Data specifications:
# - Location: All individual countries (~240 locations)
# - Scenario: Medium variant only
# - Sex: Both genders combined
# - Time period: 1950-2100 (we'll filter to 1960-2050)
# - Output: CSV file with country names, location IDs, years, and population
#
# Required packages: dplyr
# Installation: install.packages("dplyr")
#
# Usage: Rscript download_un_population_direct.R
#
# NOTE: This script downloads a ~3MB CSV file from population.un.org
# The download is fully automatic - no manual steps required!
#

# =============================================================================
# SETUP
# =============================================================================

suppressPackageStartupMessages({
  library(dplyr)
})

# Configuration
DATA_URL <- "https://population.un.org/wpp/Download/Files/1_Indicator%20%28Standard%29/CSV_FILES/WPP2024_TotalPopulationBySex.csv"
CSV_FILE <- "WPP2024_TotalPopulationBySex.csv"
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"
START_YEAR <- 1960
END_YEAR <- 2050

cat("===========================================================\n")
cat("UN Population Data Download - Direct CSV Method\n")
cat("Source: WPP2024 Bulk CSV File\n")
cat("===========================================================\n\n")

# =============================================================================
# STEP 1: DOWNLOAD OR LOCATE DATA FILE
# =============================================================================

cat("Step 1: Locating data file...\n")

if (file.exists(CSV_FILE)) {
  cat(sprintf("  ✓ Found existing file: %s\n", CSV_FILE))
  cat(sprintf("  File size: %.1f MB\n\n", file.info(CSV_FILE)$size / 1024^2))
} else {
  cat(sprintf("  File not found locally, attempting download...\n"))
  cat(sprintf("  URL: %s\n", DATA_URL))

  # Try to download the CSV file directly
  download_result <- tryCatch({
    download.file(
      url = DATA_URL,
      destfile = CSV_FILE,
      method = "auto",
      quiet = FALSE,
      mode = "wb"
    )
    TRUE
  }, error = function(e) {
    cat(sprintf("\n  ✗ Download failed: %s\n\n", e$message))
    FALSE
  })

  if (download_result && file.exists(CSV_FILE)) {
    cat(sprintf("  ✓ Download complete: %s (%.1f MB)\n\n", CSV_FILE, file.info(CSV_FILE)$size / 1024^2))
  } else {
    cat("\n===========================================================\n")
    cat("MANUAL DOWNLOAD REQUIRED\n")
    cat("===========================================================\n\n")
    cat("The automatic download failed (likely due to network restrictions).\n")
    cat("Please download the file manually:\n\n")
    cat("1. Go to: https://population.un.org/wpp/downloads\n")
    cat("2. Navigate to: Standard Projections > CSV format\n")
    cat("3. Download: WPP2024_TotalPopulationBySex.csv\n")
    cat("4. Place the CSV file in this directory\n")
    cat("5. Run this script again\n\n")
    cat("Or download directly:\n")
    cat(sprintf("   %s\n\n", DATA_URL))
    stop("Cannot proceed without data file")
  }
}

# =============================================================================
# STEP 2: READ AND FILTER DATA
# =============================================================================

cat("Step 2: Reading and filtering data...\n")
cat("  This may take a moment (file contains ~50k rows)...\n")

# Read the full CSV file
raw_data <- read.csv(CSV_FILE, stringsAsFactors = FALSE, check.names = FALSE)

cat(sprintf("  Loaded: %s rows, %d columns\n", format(nrow(raw_data), big.mark = ","), ncol(raw_data)))

# Show column names
cat("\n  Column names:\n")
cat(sprintf("    %s\n\n", paste(names(raw_data), collapse = ", ")))

# Filter the data:
# - Variant = Medium
# - Year range: 1960-2050
# - Both sexes combined
# - Exclude regional aggregates (keep only countries with ISO3 codes)

cat("  Filtering data...\n")

clean_data <- raw_data %>%
  filter(
    # Medium variant
    grepl("Medium", Variant, ignore.case = TRUE) | Variant == "Median",
    # Year range
    Time >= START_YEAR & Time <= END_YEAR,
    # Both sexes (if column exists)
    if ("Sex" %in% names(.)) Sex == "Both" | Sex == "Total" else TRUE,
    # Only countries with ISO3 codes (filter out regional aggregates)
    !is.na(ISO3_code) & ISO3_code != "" & nchar(as.character(ISO3_code)) == 3,
    # Location ID < 900 (individual countries) or = 900 (World)
    LocID < 900 | LocID == 900
  ) %>%
  select(
    Country = Location,
    LocationId = LocID,
    Year = Time,
    Population = PopTotal
  ) %>%
  mutate(
    Year = as.integer(Year),
    LocationId = as.integer(LocationId),
    Population = as.numeric(Population) * 1000  # Convert from thousands to actual count
  ) %>%
  arrange(Country, Year) %>%
  distinct()

cat(sprintf("  Processed: %s rows\n", format(nrow(clean_data), big.mark = ",")))
cat(sprintf("  Countries: %d\n", length(unique(clean_data$Country))))
cat(sprintf("  Year range: %d-%d\n\n", min(clean_data$Year), max(clean_data$Year)))

# =============================================================================
# STEP 3: EXPORT TO CSV
# =============================================================================

cat("Step 3: Exporting to CSV...\n")
write.csv(clean_data, OUTPUT_FILE, row.names = FALSE)

file_size_kb <- file.info(OUTPUT_FILE)$size / 1024
cat(sprintf("  ✓ File created: %s (%.1f KB)\n", OUTPUT_FILE, file_size_kb))

# =============================================================================
# VALIDATION & SUMMARY
# =============================================================================

cat("\n===========================================================\n")
cat("COMPLETE!\n")
cat("===========================================================\n")
cat(sprintf("Countries: %d | Rows: %s\n",
            length(unique(clean_data$Country)),
            format(nrow(clean_data), big.mark = ",")))
cat(sprintf("Year range: %d-%d | File: %s\n",
            min(clean_data$Year), max(clean_data$Year), OUTPUT_FILE))

cat("\nFirst 15 rows:\n")
print(head(clean_data, 15))

# Additional validation
duplicates <- clean_data %>%
  group_by(Country, Year) %>%
  filter(n() > 1) %>%
  nrow()

if (duplicates > 0) {
  cat(sprintf("\n⚠ WARNING: Found %d duplicate Country-Year combinations\n", duplicates))
} else {
  cat("\n✓ No duplicate Country-Year combinations\n")
}

negative_pop <- sum(clean_data$Population < 0, na.rm = TRUE)
if (negative_pop > 0) {
  cat(sprintf("⚠ WARNING: Found %d negative population values\n", negative_pop))
} else {
  cat("✓ All population values are positive\n")
}

missing_pop <- sum(is.na(clean_data$Population))
if (missing_pop > 0) {
  cat(sprintf("⚠ WARNING: Found %d missing population values\n", missing_pop))
} else {
  cat("✓ No missing population values\n")
}

cat("\n===========================================================\n")
cat("Done! Use this file for your visualizations.\n")
cat("===========================================================\n")

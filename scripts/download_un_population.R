#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Download Script
# ===================================================
#
# This script downloads total population data from the UN World Population
# Prospects 2024 bulk CSV file for all countries/areas.
#
# Data specifications:
# - Location: All individual countries + World (~240 locations)
# - Scenario: Medium variant only
# - Sex: Both genders combined
# - Time period: 1960-2050
# - Output: CSV file with country names, location IDs, years, and population
#
# Required packages: dplyr, R.utils
# Installation: install.packages(c("dplyr", "R.utils"))
#
# Usage: Rscript download_un_population.R
#

# =============================================================================
# SETUP
# =============================================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(R.utils)
})

CSV_URL <- "https://population.un.org/wpp/Download/Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_TotalPopulationBySex.csv.gz"
START_YEAR <- 1960
END_YEAR <- 2050
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"

# Regional aggregates to exclude - keep individual countries + World
exclude_list <- c(
  "More developed regions", "Less developed regions",
  "Least developed countries",
  "Less developed regions, excluding least developed countries",
  "Less developed regions, excluding China",
  "High-income countries", "Middle-income countries", "Low-income countries",
  "Upper-middle-income countries", "Lower-middle-income countries",
  "Sub-Saharan Africa", "AFRICA", "ASIA", "EUROPE",
  "LATIN AMERICA AND THE CARIBBEAN", "NORTHERN AMERICA", "OCEANIA",
  "Land-locked Developing Countries (LLDC)",
  "Small Island Developing States (SIDS)",
  "Developing regions",
  "Eastern Africa", "Middle Africa", "Northern Africa", "Southern Africa", "Western Africa",
  "Eastern Asia", "South-central Asia", "South-Eastern Asia", "Western Asia",
  "Eastern Europe", "Northern Europe", "Southern Europe", "Western Europe",
  "Caribbean", "Central America", "South America",
  "Australia/New Zealand", "Melanesia", "Micronesia", "Polynesia",
  "Central Asia", "Southern Asia",
  "Channel Islands",
  "Latin America and the Caribbean",
  "Northern America and Europe",
  "LLDC: Africa", "LLDC: Asia", "LLDC: Oceania"
)

cat("===========================================================\n")
cat("UN Population Data Download - All Countries\n")
cat("Source: WPP2024 Bulk CSV File\n")
cat("===========================================================\n\n")

# =============================================================================
# STEP 1: DOWNLOAD GZIPPED CSV FILE
# =============================================================================

cat("Step 1: Downloading CSV file from UN...\n")
temp_gz <- tempfile(fileext = ".csv.gz")
temp_csv <- tempfile(fileext = ".csv")

download_result <- tryCatch({
  download.file(CSV_URL, temp_gz, mode = "wb", quiet = FALSE)
  TRUE
}, error = function(e) {
  cat(sprintf("  ERROR: Failed to download file\n"))
  cat(sprintf("  %s\n", e$message))
  FALSE
})

if (!download_result || !file.exists(temp_gz)) {
  stop("Failed to download CSV file. Please check your internet connection.")
}

file_size_mb <- file.info(temp_gz)$size / (1024 * 1024)
cat(sprintf("  Downloaded: %.1f MB\n\n", file_size_mb))

# =============================================================================
# STEP 2: EXTRACT GZIPPED FILE
# =============================================================================

cat("Step 2: Extracting gzipped file...\n")
extract_result <- tryCatch({
  gunzip(temp_gz, temp_csv, remove = FALSE, overwrite = TRUE)
  TRUE
}, error = function(e) {
  cat(sprintf("  ERROR: Failed to extract file\n"))
  cat(sprintf("  %s\n", e$message))
  FALSE
})

if (!extract_result || !file.exists(temp_csv)) {
  stop("Failed to extract CSV file.")
}

cat("  Extraction complete\n\n")

# =============================================================================
# STEP 3: READ CSV DATA
# =============================================================================

cat("Step 3: Reading CSV data...\n")
raw_data <- tryCatch({
  # UN CSV files use pipe separator
  read.csv(temp_csv, sep = "|", stringsAsFactors = FALSE, check.names = FALSE)
}, error = function(e) {
  cat(sprintf("  ERROR: Failed to read CSV\n"))
  cat(sprintf("  %s\n", e$message))
  stop("Failed to read CSV file.")
})

cat(sprintf("  Loaded: %s rows, %d columns\n", format(nrow(raw_data), big.mark = ","), ncol(raw_data)))

# Show column names for debugging
cat("\n  Column names in CSV:\n")
cat(sprintf("    %s\n", paste(names(raw_data), collapse = ", ")))
cat("\n")

# =============================================================================
# STEP 4: FILTER AND PROCESS DATA
# =============================================================================

cat("Step 4: Filtering data...\n")

# Dynamically detect column names (handle different CSV structures)
find_column <- function(df, patterns) {
  for (pattern in patterns) {
    matches <- grep(pattern, names(df), ignore.case = TRUE, value = TRUE)
    if (length(matches) > 0) return(matches[1])
  }
  return(NA)
}

variant_col <- find_column(raw_data, c("variant", "variantlabel"))
sex_col <- find_column(raw_data, c("sexid", "sex"))
location_col <- find_column(raw_data, c("location", "locarea"))
locid_col <- find_column(raw_data, c("locid", "locationid"))
time_col <- find_column(raw_data, c("time", "year", "timemid"))
value_col <- find_column(raw_data, c("poptotal", "popfemale|popmale", "value"))

cat(sprintf("  Using columns:\n"))
cat(sprintf("    Variant: %s\n", ifelse(is.na(variant_col), "NOT FOUND", variant_col)))
cat(sprintf("    Sex: %s\n", ifelse(is.na(sex_col), "NOT FOUND", sex_col)))
cat(sprintf("    Location: %s\n", ifelse(is.na(location_col), "NOT FOUND", location_col)))
cat(sprintf("    LocationId: %s\n", ifelse(is.na(locid_col), "NOT FOUND", locid_col)))
cat(sprintf("    Time: %s\n", ifelse(is.na(time_col), "NOT FOUND", time_col)))
cat(sprintf("    Value: %s\n\n", ifelse(is.na(value_col), "NOT FOUND", value_col)))

# Check if all required columns were found
if (any(is.na(c(variant_col, sex_col, location_col, time_col, value_col)))) {
  stop("ERROR: Could not find all required columns in CSV. Check column names above.")
}

# Filter data
clean_data <- raw_data %>%
  filter(
    # Medium variant (ID = 2 or label contains "Medium")
    .data[[variant_col]] %in% c(2, "2", "Medium", "Medium variant", "Median") |
      grepl("medium", .data[[variant_col]], ignore.case = TRUE),
    # Both sexes (ID = 3 or label contains "Both")
    .data[[sex_col]] %in% c(3, "3", "Both", "Both sexes") |
      grepl("both", .data[[sex_col]], ignore.case = TRUE),
    # Year range
    as.integer(.data[[time_col]]) >= START_YEAR,
    as.integer(.data[[time_col]]) <= END_YEAR,
    # Exclude regional aggregates
    !.data[[location_col]] %in% exclude_list
  ) %>%
  select(
    Country = all_of(location_col),
    LocationId = if (!is.na(locid_col)) all_of(locid_col) else all_of(location_col),
    Year = all_of(time_col),
    Population = all_of(value_col)
  ) %>%
  mutate(
    Year = as.integer(Year),
    LocationId = as.integer(LocationId),
    Population = as.numeric(Population)
  ) %>%
  arrange(Country, Year) %>%
  distinct()

cat(sprintf("  Filtered to: %s rows\n", format(nrow(clean_data), big.mark = ",")))
cat(sprintf("  Countries: %d\n", length(unique(clean_data$Country))))
cat(sprintf("  Year range: %d-%d\n\n", min(clean_data$Year), max(clean_data$Year)))

# =============================================================================
# STEP 5: EXPORT WITH VALIDATION
# =============================================================================

cat("Step 5: Exporting to CSV...\n")
write.csv(clean_data, OUTPUT_FILE, row.names = FALSE)

file_size_kb <- file.info(OUTPUT_FILE)$size / 1024
cat(sprintf("  File created: %s (%.1f KB)\n", OUTPUT_FILE, file_size_kb))

# Cleanup temporary files
unlink(c(temp_gz, temp_csv))
cat("  Cleaned up temporary files\n")

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

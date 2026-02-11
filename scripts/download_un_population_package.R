#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Script (Using wpp2024 R Package)
# =====================================================================
#
# This script uses the wpp2024 R package to access UN World Population
# Prospects 2024 data directly - NO DOWNLOADS NEEDED!
#
# Data specifications:
# - Location: All individual countries (~240 locations)
# - Scenario: Medium variant only
# - Sex: Both genders combined
# - Time period: 1960-2050
# - Output: CSV file with country names, location IDs, years, and population
#
# Required packages: wpp2024, dplyr, devtools
# Installation: See below
#
# Usage: Rscript download_un_population_package.R
#

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

cat("===========================================================\n")
cat("UN Population Data - Using wpp2024 Package\n")
cat("Source: WPP2024 via R package (NO DOWNLOAD NEEDED!)\n")
cat("===========================================================\n\n")

# Check and install required packages
cat("Step 1: Checking required packages...\n")

# Install devtools if needed
if (!require("devtools", quietly = TRUE)) {
  cat("  Installing devtools...\n")
  install.packages("devtools", repos = "https://cloud.r-project.org")
}

# Install dplyr if needed
if (!require("dplyr", quietly = TRUE)) {
  cat("  Installing dplyr...\n")
  install.packages("dplyr", repos = "https://cloud.r-project.org")
}

# Install wpp2024 if needed
if (!require("wpp2024", quietly = TRUE)) {
  cat("  Installing wpp2024 package from GitHub...\n")
  cat("  This may take a moment...\n")
  options(timeout = 600)
  devtools::install_github("PPgp/wpp2024", quiet = TRUE)
}

# Load libraries
suppressPackageStartupMessages({
  library(wpp2024)
  library(dplyr)
})

cat("  ✓ All packages loaded\n\n")

# Configuration
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"
START_YEAR <- 1960
END_YEAR <- 2050

# =============================================================================
# STEP 2: LOAD DATA FROM PACKAGE
# =============================================================================

cat("Step 2: Loading population data from wpp2024 package...\n")

# Load the annual population data (both sexes combined, in thousands)
data(popAge1dt, package = "wpp2024")

cat(sprintf("  Loaded: %s rows, %d columns\n", format(nrow(popAge1dt), big.mark = ","), ncol(popAge1dt)))

# Show column names
cat("\n  Column names:\n")
cat(sprintf("    %s\n\n", paste(names(popAge1dt), collapse = ", ")))

# =============================================================================
# STEP 3: PROCESS AND FILTER DATA
# =============================================================================

cat("Step 3: Processing data...\n")

# Filter and aggregate data:
# - Year range: 1960-2050
# - Medium variant (scenario == 2)
# - Sum across all ages to get total population
# - Filter to countries only (exclude regional aggregates)

clean_data <- popAge1dt %>%
  filter(
    # Year range
    year >= START_YEAR & year <= END_YEAR,
    # Medium variant only (scenario 2)
    scenario == 2
  ) %>%
  # Sum population across all ages for each country-year
  group_by(country_code, name, year) %>%
  summarise(
    Population = sum(popM + popF, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  # Rename columns for consistency
  rename(
    LocationId = country_code,
    Country = name,
    Year = year
  ) %>%
  mutate(
    Year = as.integer(Year),
    LocationId = as.integer(LocationId),
    Population = Population * 1000  # Convert from thousands to actual count
  ) %>%
  arrange(Country, Year)

cat(sprintf("  Processed: %s rows\n", format(nrow(clean_data), big.mark = ",")))
cat(sprintf("  Countries: %d\n", length(unique(clean_data$Country))))
cat(sprintf("  Year range: %d-%d\n\n", min(clean_data$Year), max(clean_data$Year)))

# =============================================================================
# STEP 4: EXPORT TO CSV
# =============================================================================

cat("Step 4: Exporting to CSV...\n")
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

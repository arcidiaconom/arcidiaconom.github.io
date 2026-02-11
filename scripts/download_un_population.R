#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Download Script
# ===================================================
#
# This script downloads total population data from the UN World Population
# Prospects 2024 API for all countries/areas.
#
# Data specifications:
# - Location: All individual countries + World (~240 locations)
# - Scenario: Medium variant only
# - Sex: Both genders combined
# - Time period: 1960-2050
# - Output: CSV file with country names, location IDs, years, and population
#
# Required packages: dplyr
# Installation: install.packages("dplyr")
#
# Usage: Rscript download_un_population.R
#

# =============================================================================
# SETUP
# =============================================================================

suppressPackageStartupMessages({
  library(dplyr)
})

API_BASE_URL <- "https://population.un.org/dataportalapi/api/v1"
INDICATOR_ID <- 49  # Total Population, Both Sexes
START_YEAR <- 1960
END_YEAR <- 2050
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"

cat("===========================================================\n")
cat("UN Population Data Download - All Countries\n")
cat("Source: WPP2024 Data Portal API\n")
cat("===========================================================\n\n")

# =============================================================================
# HELPER FUNCTION
# =============================================================================

# Dynamically detect column names (handle different API response structures)
find_column <- function(df, patterns) {
  for (pattern in patterns) {
    matches <- grep(pattern, names(df), ignore.case = TRUE, value = TRUE)
    if (length(matches) > 0) return(matches[1])
  }
  return(NA)
}

# =============================================================================
# STEP 1: FETCH LOCATIONS FROM API
# =============================================================================

cat("Step 1: Fetching location list from UN API...\n")
locations_url <- paste0(API_BASE_URL, "/locations?sort=id&format=csv")

locations_data <- tryCatch({
  # API CSV files use pipe separator and have a header line to skip
  read.csv(locations_url, sep = "|", skip = 1, stringsAsFactors = FALSE, check.names = FALSE)
}, error = function(e) {
  cat(sprintf("  ERROR: Failed to fetch locations\n"))
  cat(sprintf("  %s\n", e$message))
  stop("Failed to fetch location data from API. Please check your internet connection.")
})

cat(sprintf("  Loaded: %d locations\n", nrow(locations_data)))

# Show column names for debugging
cat("\n  Column names in locations data:\n")
cat(sprintf("    %s\n\n", paste(names(locations_data), collapse = ", ")))

# =============================================================================
# STEP 2: FILTER TO INDIVIDUAL COUNTRIES
# =============================================================================

cat("Step 2: Filtering to individual countries...\n")

# Dynamically detect column names
id_col <- find_column(locations_data, c("^id$", "locid", "locationid"))
name_col <- find_column(locations_data, c("name", "location"))
iso3_col <- find_column(locations_data, c("iso3", "isocode3"))

cat(sprintf("  Using columns: Id='%s', Name='%s', Iso3='%s'\n",
            ifelse(is.na(id_col), "NOT FOUND", id_col),
            ifelse(is.na(name_col), "NOT FOUND", name_col),
            ifelse(is.na(iso3_col), "NOT FOUND", iso3_col)))

if (any(is.na(c(id_col, name_col)))) {
  stop("ERROR: Could not find required columns in locations data.")
}

# Filter to individual countries using Location ID ranges
# Individual countries have IDs in ranges:
#   - 4-894: Standard countries and territories
#   - 900: World (include this)
# Regional aggregates and special groupings have IDs >= 901
countries <- locations_data %>%
  filter(
    (.data[[id_col]] >= 4 & .data[[id_col]] < 900) |
    .data[[id_col]] == 900
  ) %>%
  select(Id = all_of(id_col), Name = all_of(name_col)) %>%
  arrange(Name)

cat(sprintf("  Filtered by ID range (4-894 + World=900)\n"))

cat(sprintf("  Selected: %d locations\n", nrow(countries)))
cat(sprintf("  Location IDs range: %d - %d\n\n", min(countries$Id), max(countries$Id)))

# =============================================================================
# STEP 3: FETCH POPULATION DATA FROM API
# =============================================================================

cat("Step 3: Fetching population data from UN API...\n")
cat("  This may take a moment...\n")

# Fetch data one country at a time to avoid 401 errors
# The API seems to have issues with batch requests
BATCH_SIZE <- 1
num_batches <- nrow(countries)
cat(sprintf("  Fetching data for %d locations (one at a time)...\n", num_batches))

all_data <- list()

for (i in 1:num_batches) {
  country <- countries[i, ]

  # Show progress every 10 countries
  if (i %% 10 == 1 || i == num_batches) {
    cat(sprintf("  Progress: %d/%d - %s... ", i, num_batches, country$Name))
  }

  # Create location ID for this country
  location_ids <- country$Id

  # Build API URL (note the trailing slash before query params)
  data_url <- paste0(
    API_BASE_URL,
    "/data/indicators/", INDICATOR_ID,
    "/locations/", location_ids,
    "/start/", START_YEAR,
    "/end/", END_YEAR,
    "/?format=csv"
  )

  batch_data <- tryCatch({
    read.csv(data_url, sep = "|", skip = 1, stringsAsFactors = FALSE, check.names = FALSE)
  }, error = function(e) {
    if (i %% 10 == 1 || i == num_batches) {
      cat(sprintf("✗\n"))
    }
    cat(sprintf("  WARNING: Failed to fetch %s (ID=%d): %s\n", country$Name, country$Id, e$message))
    return(NULL)
  })

  if (!is.null(batch_data) && nrow(batch_data) > 0) {
    all_data[[i]] <- batch_data
    if (i %% 10 == 1 || i == num_batches) {
      cat(sprintf("✓\n"))
    }
  } else {
    if (i %% 10 == 1 || i == num_batches) {
      cat(sprintf("✗ (no data)\n"))
    }
  }

  # Small delay between requests to be respectful to the API
  if (i < num_batches) {
    Sys.sleep(0.2)
  }
}

# Combine all batches
cat("\n  Combining batches...\n")
raw_data <- bind_rows(all_data)

cat(sprintf("  Total loaded: %s rows, %d columns\n", format(nrow(raw_data), big.mark = ","), ncol(raw_data)))

# Show column names for debugging
cat("\n  Column names in API response:\n")
cat(sprintf("    %s\n", paste(names(raw_data), collapse = ", ")))
cat("\n")

# =============================================================================
# STEP 4: PROCESS AND CLEAN DATA
# =============================================================================

cat("Step 4: Processing data...\n")

# Dynamically detect column names (handle different API response structures)
variant_col <- find_column(raw_data, c("variant", "variantlabel", "variantid"))
location_col <- find_column(raw_data, c("location", "locarea", "name"))
locid_col <- find_column(raw_data, c("locid", "locationid", "id"))
time_col <- find_column(raw_data, c("time", "year", "timemid", "timeperiod"))
value_col <- find_column(raw_data, c("value", "poptotal"))

cat(sprintf("  Using columns:\n"))
cat(sprintf("    Variant: %s\n", ifelse(is.na(variant_col), "NOT FOUND", variant_col)))
cat(sprintf("    Location: %s\n", ifelse(is.na(location_col), "NOT FOUND", location_col)))
cat(sprintf("    LocationId: %s\n", ifelse(is.na(locid_col), "NOT FOUND", locid_col)))
cat(sprintf("    Time: %s\n", ifelse(is.na(time_col), "NOT FOUND", time_col)))
cat(sprintf("    Value: %s\n\n", ifelse(is.na(value_col), "NOT FOUND", value_col)))

# Check if all required columns were found
if (any(is.na(c(location_col, time_col, value_col)))) {
  stop("ERROR: Could not find all required columns in API response. Check column names above.")
}

# Process data
# API for indicator 49 already filters to medium variant and both sexes
clean_data <- raw_data %>%
  {
    # Apply variant filter only if variant column exists
    if (!is.na(variant_col)) {
      filter(.,
        .data[[variant_col]] %in% c(2, "2", "Medium", "Medium variant", "Median") |
          grepl("medium", as.character(.data[[variant_col]]), ignore.case = TRUE)
      )
    } else {
      .
    }
  } %>%
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

cat(sprintf("  Processed: %s rows\n", format(nrow(clean_data), big.mark = ",")))
cat(sprintf("  Countries: %d\n", length(unique(clean_data$Country))))
cat(sprintf("  Year range: %d-%d\n\n", min(clean_data$Year), max(clean_data$Year)))

# =============================================================================
# STEP 5: EXPORT TO CSV
# =============================================================================

cat("Step 5: Exporting to CSV...\n")
write.csv(clean_data, OUTPUT_FILE, row.names = FALSE)

file_size_kb <- file.info(OUTPUT_FILE)$size / 1024
cat(sprintf("  File created: %s (%.1f KB)\n", OUTPUT_FILE, file_size_kb))

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

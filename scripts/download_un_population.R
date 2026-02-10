#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Download Script
# ===================================================
#
# This script downloads total population data from the UN World Population
# Prospects Data Portal API for all countries/areas.
#
# Data specifications:
# - Location: All individual countries + World (~240 locations)
# - Scenario: Medium variant only
# - Sex: Both genders combined
# - Time period: 1960-2050
# - Output: CSV file with country names, location IDs, years, and population
#
# Required packages: jsonlite, dplyr
# Installation: install.packages(c("jsonlite", "dplyr"))
#
# Usage: Rscript download_un_population.R
#

# =============================================================================
# SETUP
# =============================================================================

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
})

BASE_URL <- "https://population.un.org/dataportalapi/api/v1"
INDICATOR_ID <- 49  # Total population
START_YEAR <- 1960
END_YEAR <- 2050
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"

cat("===========================================================\n")
cat("UN Population Data Download - All Countries\n")
cat("===========================================================\n\n")

# =============================================================================
# STEP 1: FETCH ALL LOCATIONS WITH PAGINATION
# =============================================================================

cat("Step 1: Fetching locations...\n")
all_locations <- list()
page_num <- 1
max_pages <- 5

while (page_num <= max_pages) {
  url <- sprintf("%s/locations?pageNumber=%d&pageSize=100", BASE_URL, page_num)

  response <- tryCatch({
    fromJSON(url, flatten = TRUE)
  }, error = function(e) {
    cat(sprintf("  Warning: Page %d failed, stopping pagination\n", page_num))
    return(NULL)
  })

  if (is.null(response) || is.null(response$data) || nrow(response$data) == 0) {
    break
  }

  all_locations[[page_num]] <- response$data
  cat(sprintf("  Page %d: %d locations\n", page_num, nrow(response$data)))

  page_num <- page_num + 1
  Sys.sleep(0.5)
}

locations <- bind_rows(all_locations)
cat(sprintf("\nTotal locations fetched: %d\n", nrow(locations)))

# =============================================================================
# STEP 2: FILTER TO COUNTRIES ONLY
# =============================================================================

cat("\nStep 2: Filtering to countries...\n")

# Exclude regional aggregates - keep individual countries + World
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

# Use lowercase 'name' column
countries <- locations %>% filter(!name %in% exclude_list)
cat(sprintf("Countries to download: %d\n\n", nrow(countries)))

# =============================================================================
# STEP 3: DOWNLOAD DATA ONE LOCATION AT A TIME
# =============================================================================

cat("Step 3: Downloading population data...\n")
cat("(This will take 10-15 minutes)\n\n")

all_data <- list()
total <- nrow(countries)

for (i in 1:total) {
  loc_id <- countries$id[i]  # lowercase 'id'
  loc_name <- countries$name[i]  # lowercase 'name'

  # Progress indicator every 20 locations
  if (i %% 20 == 0) {
    cat(sprintf("  Progress: %d/%d (%.0f%%) - %s\n",
                i, total, (i/total)*100, loc_name))
  }

  # Download for SINGLE location (no batching - API doesn't support it)
  url <- sprintf("%s/data/indicators/%d/locations/%d/start/%d/end/%d",
                 BASE_URL, INDICATOR_ID, loc_id, START_YEAR, END_YEAR)

  loc_data <- tryCatch({
    # Handle pagination for data endpoint
    pages <- list()
    next_url <- url
    page <- 0

    while (!is.null(next_url) && page < 20) {
      page <- page + 1
      resp <- fromJSON(next_url, flatten = TRUE)

      if (!is.null(resp$data) && nrow(resp$data) > 0) {
        pages[[page]] <- resp$data
      }

      next_url <- resp$nextPage
    }

    if (length(pages) > 0) bind_rows(pages) else NULL

  }, error = function(e) {
    NULL  # Skip locations that fail
  })

  if (!is.null(loc_data)) {
    all_data[[i]] <- loc_data
  }

  Sys.sleep(0.15)  # Delay to avoid overwhelming API
}

cat(sprintf("\nCompleted: %d/%d locations\n", length(all_data), total))

# =============================================================================
# STEP 4: PROCESS DATA WITH LOWERCASE COLUMN NAMES
# =============================================================================

cat("\nStep 4: Processing data...\n")
raw_data <- bind_rows(all_data)

# Debug: Print actual column names
cat("\nActual column names in API response:\n")
cat(paste(names(raw_data), collapse = ", "), "\n\n")

# Find the correct column names (case-insensitive search)
variant_col <- names(raw_data)[grep("variant", names(raw_data), ignore.case = TRUE)[1]]
sex_col <- names(raw_data)[grep("sex", names(raw_data), ignore.case = TRUE)[1]]
location_col <- names(raw_data)[grep("^location$|^loc$", names(raw_data), ignore.case = TRUE)[1]]
locid_col <- names(raw_data)[grep("locid|loc.*id", names(raw_data), ignore.case = TRUE)[1]]
time_col <- names(raw_data)[grep("time|year", names(raw_data), ignore.case = TRUE)[1]]
value_col <- names(raw_data)[grep("^value$|^population$", names(raw_data), ignore.case = TRUE)[1]]

cat(sprintf("Using columns: %s, %s, %s, %s, %s, %s\n\n",
            variant_col, sex_col, location_col, locid_col, time_col, value_col))

# Filter using the actual column names
clean_data <- raw_data %>%
  filter(.data[[variant_col]] == 2, .data[[sex_col]] == 3) %>%
  select(
    Country = all_of(location_col),
    LocationId = all_of(locid_col),
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

cat(sprintf("  Final dataset: %d rows\n", nrow(clean_data)))
cat(sprintf("  Countries: %d\n", length(unique(clean_data$Country))))
cat(sprintf("  Years: %d-%d\n", min(clean_data$Year), max(clean_data$Year)))

# =============================================================================
# STEP 5: EXPORT WITH VALIDATION
# =============================================================================

cat("\nStep 5: Exporting...\n")
write.csv(clean_data, OUTPUT_FILE, row.names = FALSE)

file_size <- file.info(OUTPUT_FILE)$size / 1024
cat(sprintf("  File created: %s (%.1f KB)\n", OUTPUT_FILE, file_size))

cat("\n===========================================================\n")
cat("COMPLETE!\n")
cat("===========================================================\n")
cat(sprintf("Countries: %d | Rows: %d\n",
            length(unique(clean_data$Country)), nrow(clean_data)))

cat("\nFirst 15 rows:\n")
print(head(clean_data, 15))

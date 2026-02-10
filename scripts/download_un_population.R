#!/usr/bin/env Rscript
#
# UN World Population Prospects Data Download Script
# ===================================================
#
# This script downloads total population data from the UN World Population
# Prospects Data Portal API for:
# - Location: All countries/areas + World (238 locations)
# - Scenario: Medium variant
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

# Load required packages
cat("Loading required packages...\n")
suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
})

# API Configuration
BASE_URL <- "https://population.un.org/dataportalapi/api/v1"
START_YEAR <- 1960
END_YEAR <- 2050
OUTPUT_FILE <- "un_population_all_countries_1960_2050.csv"
BATCH_SIZE <- 30  # Number of locations to query per API call

cat("Configuration:\n")
cat(sprintf("  API Base URL: %s\n", BASE_URL))
cat(sprintf("  Year Range: %d - %d\n", START_YEAR, END_YEAR))
cat(sprintf("  Output File: %s\n\n", OUTPUT_FILE))

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

#' Make API request with error handling
#' @param url API endpoint URL
#' @return Parsed JSON response
api_request <- function(url) {
  tryCatch({
    # Use fromJSON directly - it handles HTTP requests internally
    # This approach works better with the UN API than using httr::GET()
    parsed_data <- fromJSON(url, flatten = TRUE)

    return(parsed_data)
  }, error = function(e) {
    stop(sprintf("Error making API request to %s: %s", url, e$message))
  })
}

#' Find indicator ID by searching for keyword
#' @param search_term Search keyword (e.g., "Total Population")
#' @return Indicator ID
find_indicator_id <- function(search_term = "Total Population") {
  cat(sprintf("Searching for indicator: '%s'...\n", search_term))

  url <- paste0(BASE_URL, "/indicators")
  data <- api_request(url)

  # Search in the data
  indicators <- data$data

  # Case-insensitive search
  matches <- indicators[grepl(search_term, indicators$ShortName, ignore.case = TRUE) |
                       grepl(search_term, indicators$Name, ignore.case = TRUE), ]

  if (nrow(matches) == 0) {
    stop(sprintf("No indicator found matching '%s'", search_term))
  }

  # Return first match
  indicator_id <- matches$Id[1]
  indicator_name <- matches$ShortName[1]

  cat(sprintf("  Found: %s (ID: %d)\n", indicator_name, indicator_id))
  return(indicator_id)
}

#' Get all locations (individual countries + World)
#' @return Data frame with location IDs and names
get_all_locations <- function() {
  cat("Fetching all available locations...\n")

  url <- paste0(BASE_URL, "/locations")
  data <- api_request(url)

  locations <- data$data

  # Filter to include only:
  # 1. Individual countries (LocTypeId == 4 typically represents countries)
  # 2. World (Name == "World")
  # Exclude regional aggregates and development groups

  # Check what location type values exist
  if ("LocTypeId" %in% names(locations)) {
    # Include countries (LocTypeId == 4) and World
    filtered_locations <- locations %>%
      filter(LocTypeId == 4 | Name == "World")
  } else if ("LocTypeName" %in% names(locations)) {
    # Alternative: filter by type name
    filtered_locations <- locations %>%
      filter(grepl("Country", LocTypeName, ignore.case = TRUE) | Name == "World")
  } else {
    # Fallback: exclude known aggregates by name patterns
    exclude_patterns <- c("Africa", "Asia", "Europe", "America", "Oceania",
                         "developed", "developing", "income", "SDG")
    filtered_locations <- locations %>%
      filter(Name == "World" | !grepl(paste(exclude_patterns, collapse = "|"), Name, ignore.case = TRUE))
  }

  cat(sprintf("  Found %d locations (countries + World)\n", nrow(filtered_locations)))

  return(filtered_locations)
}

#' Split location IDs into batches for API calls
#' @param location_ids Vector of location IDs
#' @param batch_size Number of locations per batch (default: 30)
#' @return List of location ID vectors
batch_locations <- function(location_ids, batch_size = 30) {
  num_batches <- ceiling(length(location_ids) / batch_size)

  batches <- lapply(1:num_batches, function(i) {
    start_idx <- (i - 1) * batch_size + 1
    end_idx <- min(i * batch_size, length(location_ids))
    location_ids[start_idx:end_idx]
  })

  return(batches)
}

#' Download population data with pagination (supports multiple locations)
#' @param indicator_id Indicator ID
#' @param location_ids Vector of location IDs
#' @param start_year Start year
#' @param end_year End year
#' @return Combined data frame with all results
download_population_data <- function(indicator_id, location_ids, start_year, end_year) {
  # Create comma-separated location string for API
  location_string <- paste(location_ids, collapse = ",")

  cat(sprintf("  Downloading data for %d location(s), years %d-%d...\n",
              length(location_ids), start_year, end_year))

  # Construct initial URL with multiple locations
  initial_url <- sprintf("%s/data/indicators/%d/locations/%s/start/%d/end/%d",
                        BASE_URL, indicator_id, location_string, start_year, end_year)

  all_data <- list()
  next_url <- initial_url
  page_count <- 0
  max_pages <- 100  # Safety limit

  # Pagination loop
  while (!is.null(next_url) && page_count < max_pages) {
    page_count <- page_count + 1
    cat(sprintf("  Fetching page %d...\n", page_count))

    response_data <- api_request(next_url)

    # Extract data
    if (!is.null(response_data$data) && length(response_data$data) > 0) {
      all_data[[page_count]] <- response_data$data
    }

    # Check for next page
    next_url <- response_data$nextPage
  }

  if (page_count >= max_pages) {
    warning("Reached maximum page limit. Data may be incomplete.")
  }

  # Combine all pages
  if (length(all_data) == 0) {
    stop("No data retrieved from API")
  }

  combined_data <- bind_rows(all_data)
  cat(sprintf("  Downloaded %d rows from %d page(s)\n", nrow(combined_data), page_count))

  return(combined_data)
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

cat("\n")
cat(paste0(strrep("=", 61), "\n"))
cat("Starting UN Population Data Download\n")
cat(paste0(strrep("=", 61), "\n\n"))

# Step 1: Discover IDs
cat("STEP 1: API Discovery\n")
cat(strrep("-", 60), "\n")

indicator_id <- tryCatch({
  find_indicator_id("Total Population")
}, error = function(e) {
  cat("Warning: Could not auto-discover indicator ID. Using fallback ID 49.\n")
  49  # Common ID for total population
})

# Get all locations (countries + World)
all_locations <- tryCatch({
  get_all_locations()
}, error = function(e) {
  stop(sprintf("Failed to retrieve locations: %s", e$message))
})

# Extract location IDs and create batches
location_ids <- all_locations$Id
location_batches <- batch_locations(location_ids, BATCH_SIZE)

cat(sprintf("\nTotal locations: %d\n", length(location_ids)))
cat(sprintf("Batches to process: %d (batch size: %d)\n", length(location_batches), BATCH_SIZE))

# Step 2: Download data in batches
cat("\n")
cat("STEP 2: Data Download (Batch Processing)\n")
cat(strrep("-", 60), "\n")

all_batch_data <- list()

for (batch_num in seq_along(location_batches)) {
  cat(sprintf("\n[Batch %d of %d]\n", batch_num, length(location_batches)))

  batch_data <- tryCatch({
    download_population_data(indicator_id, location_batches[[batch_num]],
                           START_YEAR, END_YEAR)
  }, error = function(e) {
    cat(sprintf("  ERROR in batch %d: %s\n", batch_num, e$message))
    cat("  Skipping this batch and continuing...\n")
    return(NULL)
  })

  if (!is.null(batch_data)) {
    all_batch_data[[batch_num]] <- batch_data
    cat(sprintf("  Batch %d complete: %d rows downloaded\n", batch_num, nrow(batch_data)))
  }
}

# Combine all batch results
cat("\nCombining all batch results...\n")
raw_data <- bind_rows(all_batch_data)
cat(sprintf("Total rows combined: %d\n", nrow(raw_data)))

# Step 3: Filter and process data
cat("\n")
cat("STEP 3: Data Processing\n")
cat(strrep("-", 60), "\n")

cat("Applying filters...\n")
cat("  - Medium variant\n")
cat("  - Both sexes combined\n")

# Identify available columns
available_cols <- names(raw_data)
cat(sprintf("\nAvailable columns: %s\n", paste(available_cols, collapse = ", ")))

# Filter for Medium variant and Both sexes
# The exact column names may vary, so we check for common patterns
filtered_data <- raw_data

# Filter by variant (Medium)
if ("Variant" %in% available_cols) {
  filtered_data <- filtered_data %>%
    filter(grepl("Medium", Variant, ignore.case = TRUE))
  cat(sprintf("  Filtered by Variant: %d rows remaining\n", nrow(filtered_data)))
} else if ("VariantLabel" %in% available_cols) {
  filtered_data <- filtered_data %>%
    filter(grepl("Medium", VariantLabel, ignore.case = TRUE))
  cat(sprintf("  Filtered by VariantLabel: %d rows remaining\n", nrow(filtered_data)))
} else if ("VariantId" %in% available_cols) {
  # VariantId 2 is typically Medium
  filtered_data <- filtered_data %>%
    filter(VariantId == 2)
  cat(sprintf("  Filtered by VariantId: %d rows remaining\n", nrow(filtered_data)))
}

# Filter by sex (Both sexes)
if ("Sex" %in% available_cols) {
  filtered_data <- filtered_data %>%
    filter(grepl("Both|Total", Sex, ignore.case = TRUE))
  cat(sprintf("  Filtered by Sex: %d rows remaining\n", nrow(filtered_data)))
} else if ("SexLabel" %in% available_cols) {
  filtered_data <- filtered_data %>%
    filter(grepl("Both|Total", SexLabel, ignore.case = TRUE))
  cat(sprintf("  Filtered by SexLabel: %d rows remaining\n", nrow(filtered_data)))
} else if ("SexId" %in% available_cols) {
  # SexId 3 is typically Both sexes
  filtered_data <- filtered_data %>%
    filter(SexId == 3)
  cat(sprintf("  Filtered by SexId: %d rows remaining\n", nrow(filtered_data)))
}

# Select and rename relevant columns
# Identify the location columns
location_name_col <- NULL
if ("Location" %in% available_cols) {
  location_name_col <- "Location"
} else if ("LocationLabel" %in% available_cols) {
  location_name_col <- "LocationLabel"
} else if ("LocName" %in% available_cols) {
  location_name_col <- "LocName"
}

location_id_col <- NULL
if ("LocID" %in% available_cols) {
  location_id_col <- "LocID"
} else if ("LocationId" %in% available_cols) {
  location_id_col <- "LocationId"
} else if ("Location_Id" %in% available_cols) {
  location_id_col <- "Location_Id"
}

# Identify the year column (could be TimeLabel, Year, Time, etc.)
year_col <- NULL
if ("TimeLabel" %in% available_cols) {
  year_col <- "TimeLabel"
} else if ("Year" %in% available_cols) {
  year_col <- "Year"
} else if ("Time" %in% available_cols) {
  year_col <- "Time"
}

# Identify the value column (could be Value, Population, etc.)
value_col <- NULL
if ("Value" %in% available_cols) {
  value_col <- "Value"
} else if ("Population" %in% available_cols) {
  value_col <- "Population"
}

if (is.null(location_name_col) || is.null(location_id_col) ||
    is.null(year_col) || is.null(value_col)) {
  cat("Warning: Could not identify all required columns\n")
  cat(sprintf("Location name col: %s\n", ifelse(is.null(location_name_col), "NOT FOUND", location_name_col)))
  cat(sprintf("Location ID col: %s\n", ifelse(is.null(location_id_col), "NOT FOUND", location_id_col)))
  cat(sprintf("Year col: %s\n", ifelse(is.null(year_col), "NOT FOUND", year_col)))
  cat(sprintf("Value col: %s\n", ifelse(is.null(value_col), "NOT FOUND", value_col)))
  stop("Could not identify required columns in the data")
}

# Create clean dataset with location information
clean_data <- filtered_data %>%
  select(Country = all_of(location_name_col),
         LocationId = all_of(location_id_col),
         Year = all_of(year_col),
         Population = all_of(value_col)) %>%
  mutate(Year = as.integer(Year),
         LocationId = as.integer(LocationId),
         Population = as.numeric(Population)) %>%
  arrange(Country, Year) %>%
  distinct()

cat(sprintf("\nFinal dataset: %d rows\n", nrow(clean_data)))

# Step 4: Validate data
cat("\n")
cat("STEP 4: Data Validation\n")
cat(strrep("-", 60), "\n")

# Check number of countries
num_countries <- length(unique(clean_data$Country))
cat(sprintf("Number of unique countries/locations: %d\n", num_countries))

# Check year range
year_range <- range(clean_data$Year)
cat(sprintf("Year range: %d - %d\n", year_range[1], year_range[2]))

# Check for missing values
missing_count <- sum(is.na(clean_data$Population))
cat(sprintf("Missing values: %d\n", missing_count))

# Check for negative values
negative_count <- sum(clean_data$Population < 0, na.rm = TRUE)
cat(sprintf("Negative values: %d\n", negative_count))

# Check for duplicate country-year combinations
duplicates <- clean_data %>%
  group_by(Country, Year) %>%
  filter(n() > 1) %>%
  nrow()
cat(sprintf("Duplicate country-year combinations: %d\n", duplicates))

# Display summary statistics
cat("\nPopulation statistics (in thousands):\n")
print(summary(clean_data$Population))

# Display sample countries
sample_countries <- unique(clean_data$Country)[1:min(10, num_countries)]
cat("\nSample countries included:\n")
cat(paste("  -", sample_countries, collapse = "\n"), "\n")

# Display first and last few rows
cat("\nFirst 5 rows:\n")
print(head(clean_data, 5))

cat("\nLast 5 rows:\n")
print(tail(clean_data, 5))

# Step 5: Export to CSV
cat("\n")
cat("STEP 5: Export Data\n")
cat(strrep("-", 60), "\n")

cat(sprintf("Writing data to %s...\n", OUTPUT_FILE))
write.csv(clean_data, OUTPUT_FILE, row.names = FALSE)

# Verify file creation
if (file.exists(OUTPUT_FILE)) {
  file_size <- file.info(OUTPUT_FILE)$size
  cat(sprintf("  Success! File created: %s (%.2f KB)\n", OUTPUT_FILE, file_size / 1024))
} else {
  stop("Failed to create output file")
}

# Final summary
cat("\n")
cat(paste0(strrep("=", 61), "\n"))
cat("Download Complete!\n")
cat(paste0(strrep("=", 61), "\n"))
cat(sprintf("Output file: %s\n", OUTPUT_FILE))
cat(sprintf("Total countries/locations: %d\n", num_countries))
cat(sprintf("Total rows: %d\n", nrow(clean_data)))
cat(sprintf("Year range: %d - %d\n", year_range[1], year_range[2]))
cat(sprintf("File size: %.2f MB\n", file.info(OUTPUT_FILE)$size / (1024 * 1024)))
cat("\nData structure:\n")
cat("  - Country: Country/area name\n")
cat("  - LocationId: UN location identifier\n")
cat("  - Year: 1960-2050\n")
cat("  - Population: Total population (thousands)\n")
cat("\nYou can now open the CSV file in Excel, R, or any spreadsheet application.\n")

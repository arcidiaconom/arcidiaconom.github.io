# ============================================================
# 01.Z_wb_agegrps.R
#
# Called from Stata as:
#   shell cmd /c ""$Rscript" "${root}\01.Z_wb_agegrps.R" "${data_raw}""
#
# Expects:
#   args[1] = data_raw output folder
#
# What it does:
#   - Downloads World Bank population data by 5-year age group and sex
#     from the Population Estimates and Projections database (source 40)
#     via the World Bank API v2 directly
#   - Includes individual countries plus the World aggregate (WLD)
#   - Keeps years 1990, 2020, and 2050
#   - Saves:
#       wb_population_5yr_by_sex_1990_2020_2050.csv
#       wb_population_5yr_by_sex_1990_2020_2050.xlsx
# ============================================================

# --- Install missing packages automatically ---
required_pkgs <- c("jsonlite", "dplyr", "openxlsx")
missing_pkgs  <- required_pkgs[!vapply(required_pkgs, requireNamespace,
                                        quietly = TRUE, FUN.VALUE = logical(1))]
if (length(missing_pkgs) > 0) {
  message("Installing missing packages: ", paste(missing_pkgs, collapse = ", "))
  install.packages(missing_pkgs, repos = "https://cloud.r-project.org")
}

suppressPackageStartupMessages({
  library(jsonlite)
  library(dplyr)
  library(openxlsx)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 1) {
  stop("Expected 1 argument from Stata: data_raw")
}

out_dir <- args[1]

if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
}

age_codes <- c(
  "0004","0509","1014","1519","2024","2529","3034","3539",
  "4044","4549","5054","5559","6064","6569","7074","7579","80UP"
)

sexes <- c("MA", "FE")

indicators <- as.vector(
  outer(age_codes, sexes, function(a, s) paste0("SP.POP.", a, ".", s))
)

# ---- Helper: fetch one indicator from source 40 (with pagination) ----
fetch_indicator <- function(ind) {
  all_pages <- list()
  page <- 1
  repeat {
    url <- sprintf(
      "https://api.worldbank.org/v2/country/all/indicator/%s?source=40&date=1990:2050&format=json&per_page=10000&page=%d",
      ind, page
    )
    resp <- tryCatch(
      jsonlite::fromJSON(url, flatten = TRUE),
      error = function(e) {
        warning("API error for ", ind, ": ", conditionMessage(e))
        NULL
      }
    )
    if (is.null(resp) || length(resp) < 2 || is.null(resp[[2]])) break
    all_pages[[page]] <- as.data.frame(resp[[2]], stringsAsFactors = FALSE)
    if (page >= resp[[1]]$pages) break
    page <- page + 1
  }
  if (length(all_pages) == 0) return(NULL)
  dplyr::bind_rows(all_pages)
}

# ---- Helper: get ISO3 codes for real countries (exclude aggregates) ----
fetch_country_iso3 <- function() {
  all_ent <- list()
  page <- 1
  repeat {
    url <- sprintf(
      "https://api.worldbank.org/v2/country?per_page=500&format=json&page=%d", page
    )
    resp <- jsonlite::fromJSON(url, flatten = TRUE)
    if (is.null(resp) || length(resp) < 2 || is.null(resp[[2]])) break
    all_ent[[page]] <- resp[[2]]
    if (page >= resp[[1]]$pages) break
    page <- page + 1
  }
  cdf <- dplyr::bind_rows(all_ent)
  # Real countries have a non-empty region.id (aggregates have "" or NA)
  cdf$id[!is.na(cdf$region.id) & cdf$region.id != ""]
}

message("Fetching country list from World Bank API ...")
country_iso3 <- fetch_country_iso3()
message("  Found ", length(country_iso3), " countries")

# Include the World aggregate (WLD) alongside individual countries
country_iso3 <- c(country_iso3, "WLD")
message("  Added WLD (World) aggregate")

message("Downloading ", length(indicators),
        " indicators from Population Estimates and Projections database (source 40) ...")

results <- lapply(indicators, function(ind) {
  message("  ", ind)
  fetch_indicator(ind)
})

df_raw <- dplyr::bind_rows(results)

if (nrow(df_raw) == 0) {
  stop("No data returned from the API. Check indicator codes and source 40 availability.")
}

df <- df_raw %>%
  filter(
    countryiso3code %in% country_iso3,
    as.integer(date) %in% c(1990L, 2020L, 2050L)
  ) %>%
  mutate(
    iso3c        = countryiso3code,
    country      = country.value,
    date         = as.integer(date),
    indicator_id = indicator.id,
    age_code = sub("^SP\\.POP\\.([^.]+)\\..*$", "\\1", indicator_id),
    sex_code = sub("^SP\\.POP\\.[^.]+\\.([^.]+)$", "\\1", indicator_id),
    age_group = dplyr::recode(
      age_code,
      "0004" = "0-4",
      "0509" = "5-9",
      "1014" = "10-14",
      "1519" = "15-19",
      "2024" = "20-24",
      "2529" = "25-29",
      "3034" = "30-34",
      "3539" = "35-39",
      "4044" = "40-44",
      "4549" = "45-49",
      "5054" = "50-54",
      "5559" = "55-59",
      "6064" = "60-64",
      "6569" = "65-69",
      "7074" = "70-74",
      "7579" = "75-79",
      "80UP" = "80+"
    ),
    sex = dplyr::recode(
      sex_code,
      "MA" = "Male",
      "FE" = "Female"
    )
  ) %>%
  select(
    any_of(c("iso3c", "country", "date",
             "indicator_id", "age_code", "age_group", "sex",
             "value", "unit", "obs_status"))
  ) %>%
  arrange(iso3c, date, sex, age_code)

csv_file  <- file.path(out_dir, "wb_population_5yr_by_sex_1990_2020_2050.csv")
xlsx_file <- file.path(out_dir, "wb_population_5yr_by_sex_1990_2020_2050.xlsx")

write.csv(df, csv_file, row.names = FALSE)
openxlsx::write.xlsx(df, xlsx_file, overwrite = TRUE)

message("Saved:")
message("  ", csv_file)
message("  ", xlsx_file)
message("Rows: ", nrow(df))

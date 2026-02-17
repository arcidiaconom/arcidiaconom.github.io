# ============================================================
# UN WPP Data Portal API (R) — Per-country series, 1960–2100
# Indicator 71: Percentage of total population by broad age group
# Age groups (expected): 0-14, 15-24, 25-64, 65+
# All countries (fetched from API locations endpoint)
# Variant: API often labels as "Median" (so we accept medium/median)
# Output: CSV (Excel-friendly) + XLSX
# Resilience: retries on 502/503/504
# Args:
#   arg1 = output folder (e.g., Data_Raw)
#   arg2 = token (optional; used if WPP_TOKEN env var is missing)
# ============================================================

pkgs <- c("httr", "jsonlite", "dplyr", "stringr", "readr", "writexl", "tibble", "tidyr")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(httr)
library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(writexl)
library(tibble)
library(tidyr)

# ---- Args ----
args <- commandArgs(trailingOnly = TRUE)

# ---- Token ----
token <- str_trim(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- str_trim(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd argument or set Sys.setenv(WPP_TOKEN='...').")

# ---- Parameters ----
base_url     <- "https://population.un.org/dataportalapi/api/v1"
start_year   <- 1960
end_year     <- 2100
indicator_id <- 71

# ---- Output folder (from arg1) ----
out_dir <- if (length(args) >= 1 && nzchar(args[1])) args[1] else getwd()
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = FALSE)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# ---- Helpers ----
to_snake <- function(x) {
  x <- gsub("([a-z0-9])([A-Z])", "\\1_\\2", x)
  tolower(x)
}

api_get_json <- function(url, max_tries = 8) {
  for (i in 1:max_tries) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))

    if (!http_error(r)) {
      return(fromJSON(content(r, as = "text", encoding = "UTF-8"), flatten = TRUE))
    }

    code <- status_code(r)
    body <- content(r, as = "text", encoding = "UTF-8")

    if (code %in% c(502, 503, 504)) {
      wait <- min(2^(i - 1), 30)
      message("HTTP ", code, " (try ", i, "/", max_tries, "). Waiting ", wait, "s then retrying...")
      Sys.sleep(wait)
      next
    }

    stop("HTTP ", code, " for:\n", url, "\n\n", body)
  }

  stop("Failed after ", max_tries, " tries for:\n", url)
}

make_url <- function(location_id, pageNumber = 1, pageSize = 400) {
  paste0(
    base_url,
    "/data/indicators/", indicator_id,
    "/locations/", location_id,
    "/start/", start_year,
    "/end/", end_year,
    "/?format=json",
    "&pageNumber=", pageNumber,
    "&pageSize=", pageSize
  )
}

api_get_all_pages <- function(location_id, pageSize = 400) {
  first <- api_get_json(make_url(location_id, pageNumber = 1, pageSize = pageSize))

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(make_url(location_id, pageNumber = p, pageSize = pageSize))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

pick1 <- function(df, candidates) {
  candidates <- candidates[candidates %in% names(df)]
  if (length(candidates) == 0) return(rep(NA, nrow(df)))
  df[[candidates[1]]]
}

# Normalize age group labels into our 4 buckets
normalize_age_group <- function(x) {
  x <- str_to_lower(str_trim(as.character(x)))
  x <- str_replace_all(x, "\\s+", "")
  x <- str_replace_all(x, "\u2013", "-")      # en dash -> hyphen
  x <- str_replace_all(x, "to", "-")

  if (str_detect(x, "^0-?14")) return("0-14")
  if (str_detect(x, "^15-?24")) return("15-24")
  if (str_detect(x, "^25-?64")) return("25-64")
  if (str_detect(x, "^65\\+|^65andover|^65-?\\d+|^65$")) return("65+")
  return(NA_character_)
}

# ---- Fetch list of countries ----
message("Fetching list of countries from the API ...")

fetch_locations <- function(pageSize = 100) {
  url <- paste0(base_url, "/locations?pageSize=", pageSize, "&pageNumber=1")
  first <- api_get_json(url)

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      url_p <- paste0(base_url, "/locations?pageSize=", pageSize, "&pageNumber=", p)
      res <- api_get_json(url_p)
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

locations_raw <- fetch_locations()
names(locations_raw) <- to_snake(names(locations_raw))

# Filter to countries only (locationType / type == "Country/Area" or similar)
type_col <- pick1(locations_raw, c("type", "location_type", "loc_type", "type_name"))
id_col   <- pick1(locations_raw, c("id", "location_id", "loc_id"))
name_col <- pick1(locations_raw, c("name", "location", "location_name", "loc_name"))
iso3_col <- pick1(locations_raw, c("iso3", "iso3_code", "iso_3", "iso"))

countries <- tibble(
  id   = as.integer(id_col),
  name = as.character(name_col),
  iso3 = as.character(iso3_col),
  type = as.character(type_col)
) %>%
  filter(str_detect(str_to_lower(type), "country"))

message("Found ", nrow(countries), " countries.")

if (nrow(countries) == 0) {
  stop(
    "No countries found. Available location types: ",
    paste(unique(type_col), collapse = ", ")
  )
}

# ---- Download data for each country ----
all_results <- list()
n_countries <- nrow(countries)

for (i in seq_len(n_countries)) {
  cid   <- countries$id[i]
  cname <- countries$name[i]
  ciso  <- countries$iso3[i]

  message(sprintf("[%d/%d] Downloading: %s (id=%d, iso3=%s) ...",
                  i, n_countries, cname, cid, ciso))

  raw <- tryCatch(
    api_get_all_pages(location_id = cid, pageSize = 400),
    error = function(e) {
      message("  ERROR for ", cname, ": ", conditionMessage(e))
      return(tibble())
    }
  )

  if (nrow(raw) == 0) {
    message("  No data for ", cname, ". Skipping.")
    next
  }

  names(raw) <- to_snake(names(raw))

  sex_any     <- pick1(raw, c("sex", "sex_label", "sexlabel"))
  variant_any <- pick1(raw, c("variant", "variant_label", "variant_short_name", "variantshortname"))
  year_any    <- suppressWarnings(as.integer(pick1(raw, c("time_label", "time", "year"))))
  value_any   <- suppressWarnings(as.numeric(pick1(raw, c("value"))))
  age_any     <- pick1(raw, c("age_label", "agelabel", "age_group", "agegroup",
                               "age_group_label", "agegrouplabel"))

  df <- tibble(
    Year    = year_any,
    Sex     = sex_any,
    Variant = variant_any,
    Value   = value_any,
    AgeRaw  = age_any
  ) %>%
    filter(!is.na(Year), Year >= start_year, Year <= end_year) %>%
    mutate(
      var_l    = str_to_lower(str_trim(Variant)),
      sex_l    = str_to_lower(str_trim(Sex)),
      AgeGroup = vapply(AgeRaw, normalize_age_group, FUN.VALUE = character(1))
    ) %>%
    filter(var_l %in% c("medium", "median")) %>%
    { if (any(!is.na(.$Sex))) filter(., sex_l %in% c("both sexes", "both")) else . } %>%
    filter(!is.na(AgeGroup))

  if (nrow(df) == 0) {
    message("  No rows after filtering for ", cname, ". Skipping.")
    next
  }

  # Reshape to wide (one row per year)
  wide <- df %>%
    select(Year, AgeGroup, Value) %>%
    group_by(Year, AgeGroup) %>%
    summarise(Value = dplyr::first(Value), .groups = "drop") %>%
    tidyr::pivot_wider(names_from = AgeGroup, values_from = Value) %>%
    arrange(Year) %>%
    mutate(
      Country  = cname,
      ISO3     = ciso,
      LocID    = cid
    )

  all_results[[length(all_results) + 1]] <- wide

  # Brief pause to be respectful to the API
  Sys.sleep(0.3)
}

# ---- Combine all countries ----
if (length(all_results) == 0) {
  stop("No data collected for any country.")
}

combined <- bind_rows(all_results)

# Standardize column names (some countries may lack certain age groups)
expected_age_cols <- c("0-14", "15-24", "25-64", "65+")
for (col in expected_age_cols) {
  if (!col %in% names(combined)) combined[[col]] <- NA_real_
}

# Reorder and rename columns
combined <- combined %>%
  select(Country, ISO3, LocID, Year,
         `0-14`, `15-24`, `25-64`, `65+`) %>%
  rename(
    Share_0_14   = `0-14`,
    Share_15_24  = `15-24`,
    Share_25_64  = `25-64`,
    Share_65plus = `65+`
  ) %>%
  arrange(Country, Year)

message("Total rows: ", nrow(combined),
        " (", length(unique(combined$Country)), " countries)")

# ---- Export ----
out_csv  <- file.path(out_dir, sprintf("WPP_countries_agegroups_%d_%d.csv", start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_countries_agegroups_%d_%d.xlsx", start_year, end_year))

write_excel_csv(combined, out_csv)
write_xlsx(combined, out_xlsx)

message("Saved files:")
message(" - ", out_csv)
message(" - ", out_xlsx)
message("Output folder: ", out_dir)

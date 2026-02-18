# ============================================================
# UN WPP Data Portal API (R) — Countries, Indicator 49 (Population)
# OPTIMIZED VERSION
#
# Key speed improvements over the original:
#  1. Batched location IDs — the API accepts comma-separated IDs in a
#     single request, so ~230 individual calls become ~5 batch calls.
#  2. Larger page size (1000 vs 400) — fewer pagination round-trips.
#  3. Parallel batch fetching via future.apply — batches run concurrently.
#  4. Per-batch checkpointing instead of per-country.
#
# Indicator:
#  - 49: Total population by sex
# Filters:
#  - Variant: "Median"/"Medium" when variant exists
#  - Sex: Both sexes ONLY when sex exists
# Output:
#  - CSV + XLSX with Country x Year panel
#  - Checkpoint CSV written during download
#
# Resilience:
#  - Retries on 502/503/504 with exponential backoff
#  - Skips 404 (no data for that batch)
#
# Args:
#   arg1 = output folder (e.g., Data_Raw)
#   arg2 = token (optional; used if WPP_TOKEN env var is missing)
#   arg3 = optional subset:
#          - comma-separated ISO3 (e.g., "USA,ARG,JPN")
#          - OR comma-separated LocationId (e.g., "840,32,392")
# ============================================================

# ---------- Packages ----------
pkgs <- c("httr", "jsonlite", "dplyr", "stringr", "readr", "writexl",
          "tibble", "future", "future.apply")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(httr)
library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(writexl)
library(tibble)
library(future)
library(future.apply)

# ---------- Args ----------
args <- commandArgs(trailingOnly = TRUE)

# ---------- Token ----------
token <- str_trim(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- str_trim(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd argument or set Sys.setenv(WPP_TOKEN='...').")

# ---------- Parameters ----------
base_url   <- "https://population.un.org/dataportalapi/api/v1"
indicator  <- 49
start_year <- 1960
end_year   <- 2100
batch_size <- 50   # locations per API request (keeps URLs safe length)
page_size  <- 1000 # rows per page (max supported by the API)

# ---------- Output folder ----------
out_dir <- if (length(args) >= 1 && nzchar(args[1])) args[1] else getwd()
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = FALSE)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# ---------- Helpers ----------
to_snake <- function(x) {
  x <- gsub("([a-z0-9])([A-Z])", "\\1_\\2", x)
  tolower(x)
}

pick1 <- function(df, candidates) {
  candidates <- candidates[candidates %in% names(df)]
  if (length(candidates) == 0) return(rep(NA, nrow(df)))
  df[[candidates[1]]]
}

api_get_json <- function(url, max_tries = 8) {
  for (i in seq_len(max_tries)) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))

    if (!http_error(r)) {
      return(fromJSON(content(r, as = "text", encoding = "UTF-8"), flatten = TRUE))
    }

    code <- status_code(r)
    body <- content(r, as = "text", encoding = "UTF-8")

    if (code %in% c(502, 503, 504)) {
      wait <- min(2^(i - 1), 60)
      message("  HTTP ", code, " (try ", i, "/", max_tries, "). Retrying in ", wait, "s ...")
      Sys.sleep(wait)
      next
    }

    stop("HTTP ", code, " for:\n", url, "\n\n", body)
  }
  stop("Failed after ", max_tries, " tries for:\n", url)
}

# ---------- Fetch all pages for a single URL ----------
api_get_all_pages <- function(base_data_url) {
  first <- api_get_json(paste0(base_data_url, "&pageNumber=1&pageSize=", page_size))

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(paste0(base_data_url, "&pageNumber=", p, "&pageSize=", page_size))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

# ---------- Locations ----------
make_loc_url <- function(pageNumber = 1, pageSize = 1000) {
  paste0(base_url, "/locations/?format=json",
         "&pageNumber=", pageNumber,
         "&pageSize=", pageSize,
         "&sort=id")
}

fetch_all_locations <- function() {
  first <- api_get_json(make_loc_url(1, 1000))
  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(make_loc_url(p, 1000))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }
  if (length(out) == 0) tibble() else bind_rows(out)
}

message("Downloading locations list ...")
loc_raw <- fetch_all_locations()
if (nrow(loc_raw) == 0) stop("No locations returned.")
names(loc_raw) <- to_snake(names(loc_raw))

loc_df <- tibble(
  LocationId   = suppressWarnings(as.integer(pick1(loc_raw, c("id", "location_id")))),
  Location     = as.character(pick1(loc_raw, c("name", "location_name"))),
  ISO2         = as.character(pick1(loc_raw, c("iso2", "iso2_code", "iso_2"))),
  ISO3         = as.character(pick1(loc_raw, c("iso3", "iso3_code", "iso_3"))),
  LocationType = as.character(pick1(loc_raw, c("location_type_label", "locationtypelabel",
                                                "location_type", "locationtype")))
) %>%
  filter(!is.na(LocationId), !is.na(Location)) %>%
  mutate(
    ISO2   = ifelse(nzchar(str_trim(ISO2)), str_trim(ISO2), NA_character_),
    ISO3   = ifelse(nzchar(str_trim(ISO3)), str_trim(ISO3), NA_character_),
    loc_l  = str_to_lower(str_trim(Location)),
    type_l = str_to_lower(str_trim(LocationType))
  )

# Country selection
type_has_known <- any(loc_df$type_l %in% c("country/area", "country or area",
                                            "country", "area"), na.rm = TRUE)

if (type_has_known) {
  message("Using LocationType to identify countries/areas ...")
  countries <- loc_df %>%
    filter(loc_l != "world",
           type_l %in% c("country/area", "country or area", "country", "area")) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)
} else {
  message("LocationType not usable; using ISO3-based country selection ...")
  countries <- loc_df %>%
    mutate(iso3_ok = !is.na(ISO3) &
             nchar(str_trim(ISO3)) == 3 &
             str_detect(str_trim(ISO3), "^[A-Za-z]{3}$")) %>%
    filter(loc_l != "world", iso3_ok) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)
}

message("Locations kept as countries/areas: ", nrow(countries))
if (nrow(countries) == 0) {
  stop("After filtering, no countries found.\n",
       "Tip: print unique(loc_df$LocationType) to see available labels.")
}

# Optional subset from arg3
if (length(args) >= 3 && nzchar(args[3])) {
  sel <- str_split(args[3], ",", simplify = TRUE)
  sel <- str_trim(sel[sel != ""])

  if (length(sel) > 0) {
    if (all(str_detect(sel, "^[0-9]+$"))) {
      countries <- countries %>% filter(LocationId %in% as.integer(sel))
      message("Subset selected by LocationId. Countries kept: ", nrow(countries))
    } else {
      sel_iso3 <- toupper(sel)
      countries <- countries %>% filter(toupper(ISO3) %in% sel_iso3)
      message("Subset selected by ISO3. Countries kept: ", nrow(countries))
    }
  }
}

if (nrow(countries) == 0) stop("After filtering/subsetting, no countries left to download.")

# ---------- Build batched URL for multiple locations ----------
make_batch_url <- function(indicator_id, location_ids) {
  ids_str <- paste(location_ids, collapse = ",")
  paste0(base_url,
         "/data/indicators/", indicator_id,
         "/locations/", ids_str,
         "/start/", start_year,
         "/end/", end_year,
         "/?format=json")
}

# ---------- Fetch + filter one batch of locations ----------
fetch_batch <- function(indicator_id, location_ids) {
  url <- make_batch_url(indicator_id, location_ids)

  raw <- tryCatch(
    api_get_all_pages(url),
    error = function(e) {
      msg <- conditionMessage(e)
      if (grepl("HTTP 404", msg, fixed = TRUE)) {
        message("  -> 404 for batch. Skipping.")
        return(tibble())
      }
      stop(e)
    }
  )

  if (nrow(raw) == 0) return(tibble())
  names(raw) <- to_snake(names(raw))

  # Extract columns
  loc_id_col  <- suppressWarnings(as.integer(pick1(raw, c("location_id", "locationid", "id"))))
  sex_col     <- pick1(raw, c("sex", "sex_label", "sexlabel"))
  variant_col <- pick1(raw, c("variant", "variant_label", "variant_short_name", "variantshortname"))
  year_col    <- suppressWarnings(as.integer(pick1(raw, c("time_label", "time", "year"))))
  value_col   <- suppressWarnings(as.numeric(pick1(raw, c("value"))))

  df <- tibble(
    LocationId = loc_id_col,
    Year       = year_col,
    Sex        = sex_col,
    Variant    = variant_col,
    Value      = value_col
  ) %>%
    filter(!is.na(Year), Year >= start_year, Year <= end_year) %>%
    mutate(
      var_l = str_to_lower(str_trim(Variant)),
      sex_l = str_to_lower(str_trim(Sex))
    )

  # Variant filter (only if variant column exists)
  if (!all(is.na(df$var_l))) df <- df %>% filter(var_l %in% c("medium", "median"))

  # Both sexes filter (only if sex column exists)
  if (!all(is.na(df$sex_l))) df <- df %>% filter(sex_l %in% c("both sexes", "both"))

  df %>%
    group_by(LocationId, Year) %>%
    summarise(Total_Population = mean(Value, na.rm = TRUE), .groups = "drop")
}

# ---------- Split locations into batches ----------
all_loc_ids <- countries$LocationId
n_batches   <- ceiling(length(all_loc_ids) / batch_size)
batches     <- split(all_loc_ids, ceiling(seq_along(all_loc_ids) / batch_size))

message(sprintf("\nFetching indicator %d for %d locations in %d batches (batch_size=%d, page_size=%d) ...\n",
                indicator, length(all_loc_ids), n_batches, batch_size, page_size))

# ---------- Checkpoint file ----------
checkpoint_csv <- file.path(out_dir, sprintf("WPP_indicator49_population_checkpoint_%d_%d.csv",
                                             start_year, end_year))
if (file.exists(checkpoint_csv)) file.remove(checkpoint_csv)

# ---------- Parallel plan (use all available cores) ----------
plan(multisession, workers = min(n_batches, availableCores(), 6))

# ---------- Fetch all batches in parallel ----------
t0 <- Sys.time()

batch_results <- future_lapply(seq_along(batches), function(b) {
  loc_ids <- batches[[b]]
  message(sprintf("  Batch %d/%d  (%d locations) ...", b, length(batches), length(loc_ids)))
  fetch_batch(indicator, loc_ids)
}, future.seed = TRUE)

elapsed <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
message(sprintf("\nAll batches done in %.1f seconds.", elapsed))

# ---------- Combine and build full panel ----------
pop_all <- bind_rows(batch_results)

# Build the full Year grid for every country and left-join the data
year_grid <- tibble(Year = start_year:end_year)

country_lookup <- countries %>%
  select(LocationId, Location, ISO2, ISO3)

final <- country_lookup %>%
  tidyr::crossing(year_grid) %>%
  left_join(pop_all, by = c("LocationId", "Year")) %>%
  select(LocationId, ISO3, ISO2, Location, Year, Total_Population) %>%
  arrange(Location, Year)

# ---------- Write checkpoint ----------
write_csv(final, checkpoint_csv)

# ---------- Write final outputs ----------
out_csv  <- file.path(out_dir, sprintf("WPP_countries_pop_%d_%d.csv", start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_countries_pop_%d_%d.xlsx", start_year, end_year))

write_excel_csv(final, out_csv)
write_xlsx(final, out_xlsx)

# ---------- Reset parallel plan ----------
plan(sequential)

# ---------- Summary ----------
message("\nSaved files:")
message("  - ", out_csv)
message("  - ", out_xlsx)
message("Checkpoint:")
message("  - ", checkpoint_csv)
message("Rows: ", nrow(final))
message("Countries: ", n_distinct(final$LocationId))
message("Output folder: ", out_dir)
message(sprintf("Total elapsed: %.1f seconds", elapsed))

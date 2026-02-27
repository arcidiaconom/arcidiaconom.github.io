# ============================================================
# UN WPP Data Portal API (R) — Countries, Indicator 19 (TFR)
# Indicator:
#  - 19: Total fertility rate
# Filters:
#  - Variant: "Median"/"Medium" when variant exists
#  - Sex: Both sexes ONLY when sex exists
# Output:
#  - CSV + XLSX with Country x Year panel
#
# Resilience:
#  - Retries on 502/503/504 with exponential backoff
#  - Skips 404 (no data for that location/indicator)
#
# Args:
#   arg1 = output folder (default: working directory)
#   arg2 = API token  (fallback if WPP_TOKEN env var is unset)
#   arg3 = optional comma-separated ISO3 codes or LocationIds
# ============================================================

# ---------- Packages ----------
pkgs <- c("httr", "jsonlite", "dplyr", "readr", "writexl")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) {
  if (!interactive()) stop("Missing packages: ", paste(to_install, collapse = ", "))
  install.packages(to_install)
}

library(httr)
library(jsonlite)
library(dplyr)
library(readr)
library(writexl)

# ---------- Args / Token ----------
args <- commandArgs(trailingOnly = TRUE)

token <- trimws(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- trimws(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd arg or set WPP_TOKEN env var.")

# ---------- Parameters ----------
base_url   <- "https://population.un.org/dataportalapi/api/v1"
indicator  <- 19
start_year <- 1960
end_year   <- 2100

# ---------- Output folder ----------
out_dir <- if (length(args) >= 1 && nzchar(args[1])) args[1] else getwd()
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = FALSE)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# ---------- Helpers ----------

to_snake <- function(x) tolower(gsub("([a-z0-9])([A-Z])", "\\1_\\2", x))

pick1 <- function(df, candidates) {
  found <- intersect(candidates, names(df))
  if (length(found) == 0) return(rep(NA, nrow(df)))
  df[[found[1]]]
}

api_get_json <- function(url, max_tries = 6) {
  for (i in seq_len(max_tries)) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))
    if (!http_error(r))
      return(fromJSON(content(r, "text", encoding = "UTF-8"), flatten = TRUE))

    code <- status_code(r)
    if (code %in% c(502, 503, 504)) {
      wait <- min(2^(i - 1), 60)
      message("HTTP ", code, " (try ", i, "/", max_tries, "). Retrying in ", wait, "s...")
      Sys.sleep(wait)
      next
    }
    stop("HTTP ", code, " for:\n", url, "\n\n", content(r, "text", encoding = "UTF-8"))
  }
  stop("Failed after ", max_tries, " tries for:\n", url)
}

# Generic paginated fetcher — works for any endpoint URL pattern
api_get_all_pages <- function(make_url, page_size) {
  first <- api_get_json(make_url(1, page_size))
  pages <- first$pages %||% 1
  out <- list(first$data)

  for (p in seq_len(pages)[-1]) {
    d <- api_get_json(make_url(p, page_size))$data
    if (!is.null(d) && NROW(d) > 0) out[[length(out) + 1]] <- d
  }

  if (length(out) == 0 || all(vapply(out, is.null, logical(1)))) tibble() else bind_rows(out)
}

# ---------- Locations ----------

message("Downloading locations list ...")

loc_raw <- api_get_all_pages(
  make_url = function(pg, ps) {
    paste0(base_url, "/locations/?format=json",
           "&pageNumber=", pg, "&pageSize=", ps, "&sort=id")
  },
  page_size = 1000
)
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
    ISO2 = ifelse(nzchar(trimws(ISO2)), trimws(ISO2), NA_character_),
    ISO3 = ifelse(nzchar(trimws(ISO3)), trimws(ISO3), NA_character_)
  )

# Country selection:
# 1) If LocationType looks usable, use it.
# 2) Otherwise fall back to ISO3-based heuristic.
type_l <- tolower(trimws(loc_df$LocationType))
type_has_known <- any(type_l %in% c("country/area", "country or area", "country", "area"), na.rm = TRUE)

if (type_has_known) {
  message("Using LocationType to identify countries/areas ...")
  countries <- loc_df %>%
    filter(
      tolower(trimws(Location)) != "world",
      tolower(trimws(LocationType)) %in% c("country/area", "country or area", "country", "area")
    ) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)
} else {
  message("LocationType not usable; using ISO3-based country selection ...")
  countries <- loc_df %>%
    filter(
      tolower(trimws(Location)) != "world",
      !is.na(ISO3), nchar(trimws(ISO3)) == 3, grepl("^[A-Za-z]{3}$", trimws(ISO3))
    ) %>%
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
  sel <- trimws(unlist(strsplit(args[3], ",")))
  sel <- sel[nzchar(sel)]
  if (length(sel) > 0) {
    if (all(grepl("^[0-9]+$", sel))) {
      countries <- filter(countries, LocationId %in% as.integer(sel))
      message("Subset by LocationId. Countries kept: ", nrow(countries))
    } else {
      countries <- filter(countries, toupper(ISO3) %in% toupper(sel))
      message("Subset by ISO3. Countries kept: ", nrow(countries))
    }
  }
}
if (nrow(countries) == 0) stop("After subsetting, no countries left to download.")

# ---------- Data download ----------

get_indicator_raw <- function(indicator_id, location_id) {
  raw <- tryCatch(
    api_get_all_pages(
      make_url = function(pg, ps) {
        paste0(base_url, "/data/indicators/", indicator_id,
               "/locations/", location_id,
               "/start/", start_year, "/end/", end_year,
               "/?format=json&pageNumber=", pg, "&pageSize=", ps)
      },
      page_size = 400
    ),
    error = function(e) {
      if (grepl("HTTP 404", conditionMessage(e), fixed = TRUE)) {
        message("    -> 404 (no data). Skipping.")
        return(tibble())
      }
      stop(e)
    }
  )
  if (nrow(raw) == 0) return(tibble())
  names(raw) <- to_snake(names(raw))
  raw
}

filter_common <- function(df) {
  variant <- tolower(trimws(pick1(df, c("variant", "variant_label", "variant_short_name", "variantshortname"))))
  sex     <- tolower(trimws(pick1(df, c("sex", "sex_label", "sexlabel"))))
  year    <- suppressWarnings(as.integer(pick1(df, c("time_label", "time", "year"))))
  value   <- suppressWarnings(as.numeric(pick1(df, c("value"))))

  keep <- !is.na(year) & year >= start_year & year <= end_year
  if (!all(is.na(variant))) keep <- keep & variant %in% c("medium", "median")
  if (!all(is.na(sex)))     keep <- keep & sex %in% c("both sexes", "both")

  tibble(Year = year[keep], Value = value[keep])
}

# ---------- Main loop ----------

checkpoint_csv <- file.path(out_dir, sprintf("WPP_indicator19_tfr_checkpoint_%d_%d.csv", start_year, end_year))
# Write header once
writeLines("LocationId,ISO3,ISO2,Location,Year,Total_Fertility_Rate", checkpoint_csv)

results <- vector("list", nrow(countries))

for (i in seq_len(nrow(countries))) {
  loc_id   <- countries$LocationId[i]
  loc_name <- countries$Location[i]
  iso2     <- countries$ISO2[i]
  iso3     <- countries$ISO3[i]

  message(sprintf("[%d/%d] %s (%s) ...",
                  i, nrow(countries), loc_name, ifelse(is.na(iso3), "NA", iso3)))

  raw <- get_indicator_raw(indicator, loc_id)

  if (nrow(raw) == 0) {
    results[[i]] <- tibble(
      LocationId = integer(), ISO3 = character(), ISO2 = character(),
      Location = character(), Year = integer(), Total_Fertility_Rate = numeric()
    )
    next
  }

  tfr <- filter_common(raw) %>%
    group_by(Year) %>%
    summarise(Total_Fertility_Rate = first(Value), .groups = "drop")

  panel_i <- tfr %>%
    mutate(LocationId = loc_id, Location = loc_name, ISO2 = iso2, ISO3 = iso3) %>%
    select(LocationId, ISO3, ISO2, Location, Year, Total_Fertility_Rate)

  results[[i]] <- panel_i

  # Append to checkpoint (no header — already written)
  write.table(panel_i, file = checkpoint_csv, sep = ",",
              row.names = FALSE, col.names = FALSE, append = TRUE)
}

final <- bind_rows(results) %>% arrange(Location, Year)

# ---------- Export ----------
out_csv  <- file.path(out_dir, sprintf("WPP_countries_tfr_%d_%d.csv",  start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_countries_tfr_%d_%d.xlsx", start_year, end_year))

write_excel_csv(final, out_csv)
write_xlsx(final, out_xlsx)

message("Saved:")
message("  ", out_csv)
message("  ", out_xlsx)
message("Rows: ", nrow(final), "  |  Countries: ", n_distinct(final$LocationId))

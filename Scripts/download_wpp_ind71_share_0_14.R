# ============================================================
# UN WPP Data Portal API (R) — Countries, Indicator 71 (0-14 only)
# Indicator:
#  - 71: Percentage of total population by broad age group
# Keep ONLY age group: 0-14
# Filters:
#  - Variant: "Median"/"Medium" when variant exists
#  - Sex: Both sexes ONLY when sex exists
# Output:
#  - CSV + XLSX with Country×Year panel (Share_0_14 only)
#  - Running checkpoint CSV during the loop
#
# Resilience:
#  - Retries on 502/503/504 with exponential backoff
#  - Skips 404 (no data for that location/indicator)
#
# Args:
#   arg1 = output folder (e.g., Data_Raw)
#   arg2 = token (optional; used if WPP_TOKEN env var is missing)
#   arg3 = optional subset:
#          - comma-separated ISO3 (e.g., "USA,ARG,JPN")
#          - OR comma-separated LocationId (e.g., "840,32,392")
# ============================================================

# ---------- Packages ----------
pkgs <- c("httr","jsonlite","dplyr","stringr","readr","writexl","tibble")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(httr)
library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(writexl)
library(tibble)

# ---------- Args ----------
args <- commandArgs(trailingOnly = TRUE)

# ---------- Token ----------
token <- str_trim(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- str_trim(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd argument or set Sys.setenv(WPP_TOKEN='...').")

# ---------- Parameters ----------
base_url   <- "https://population.un.org/dataportalapi/api/v1"
indicator  <- 71
start_year <- 1960
end_year   <- 2100

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
  for (i in 1:max_tries) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))

    if (!http_error(r)) {
      return(fromJSON(content(r, as = "text", encoding = "UTF-8"), flatten = TRUE))
    }

    code <- status_code(r)
    body <- content(r, as = "text", encoding = "UTF-8")

    if (code %in% c(502, 503, 504)) {
      wait <- min(2^(i - 1), 60)
      message("HTTP ", code, " (try ", i, "/", max_tries, "). Waiting ", wait, "s then retrying...")
      Sys.sleep(wait)
      next
    }

    stop("HTTP ", code, " for:\n", url, "\n\n", body)
  }

  stop("Failed after ", max_tries, " tries for:\n", url)
}

# ---------- Locations ----------
make_loc_url <- function(pageNumber = 1, pageSize = 1000) {
  paste0(
    base_url,
    "/locations/?format=json",
    "&pageNumber=", pageNumber,
    "&pageSize=", pageSize,
    "&sort=id"
  )
}

api_get_all_location_pages <- function(pageSize = 1000) {
  first <- api_get_json(make_loc_url(1, pageSize))

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(make_loc_url(p, pageSize))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

message("Downloading locations list ...")
loc_raw <- api_get_all_location_pages(pageSize = 1000)
if (nrow(loc_raw) == 0) stop("No locations returned.")
names(loc_raw) <- to_snake(names(loc_raw))

loc_df <- tibble(
  LocationId   = suppressWarnings(as.integer(pick1(loc_raw, c("id","location_id")))),
  Location     = as.character(pick1(loc_raw, c("name","location_name"))),
  ISO2         = as.character(pick1(loc_raw, c("iso2","iso2_code","iso_2"))),
  ISO3         = as.character(pick1(loc_raw, c("iso3","iso3_code","iso_3"))),
  LocationType = as.character(pick1(loc_raw, c("location_type_label","locationtypelabel","location_type","locationtype"))),
  TypeId       = suppressWarnings(as.integer(pick1(loc_raw, c("loc_type_id","location_type_id","type_id","type","location_type"))))
) %>%
  filter(!is.na(LocationId), !is.na(Location)) %>%
  mutate(
    ISO2 = ifelse(nzchar(str_trim(ISO2)), str_trim(ISO2), NA_character_),
    ISO3 = ifelse(nzchar(str_trim(ISO3)), str_trim(ISO3), NA_character_),
    loc_l  = str_to_lower(str_trim(Location)),
    type_l = str_to_lower(str_trim(LocationType))
  )

# ---------- Country filtering (three strategies) ----------

# Known non-country location IDs in the UN WPP system.
# These are regions, sub-regions, development groups, income groups,
# and other aggregates that happen to have 3-letter codes.
non_country_ids <- c(
  # World
  900,
  # Major areas / continents
  903, 904, 905, 908, 909, 935,
  # SDG regions
  941, 942, 943, 944, 945, 946, 947, 948, 949, 950,
  # Sub-regions
  910, 911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928,
  # Development groups
  901, 902, 934, 1503,
  # Income groups
  1500, 1501, 1502, 1517,
  # Other aggregates
  1636, 1637, 1830, 1832, 1833, 1835
)

# Strategy 1: Use numeric TypeId if available (4 = Country/Area in UN WPP)
type_id_available <- !all(is.na(loc_df$TypeId))
if (type_id_available) {
  country_type_id <- 4
  type_id_countries <- loc_df %>%
    filter(TypeId == country_type_id) %>%
    nrow()
  # Only use this strategy if it yields a reasonable number of countries (150+)
  type_id_usable <- type_id_countries >= 150
} else {
  type_id_usable <- FALSE
}

# Strategy 2: Use LocationType label strings
type_label_known <- any(loc_df$type_l %in% c("country/area","country or area","country","area"), na.rm = TRUE)

if (type_id_usable) {
  message("Using numeric TypeId (== 4) to identify countries/areas ...")
  countries <- loc_df %>%
    filter(
      loc_l != "world",
      TypeId == country_type_id
    ) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)

} else if (type_label_known) {
  message("Using LocationType label to identify countries/areas ...")
  countries <- loc_df %>%
    filter(
      loc_l != "world",
      type_l %in% c("country/area","country or area","country","area")
    ) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)

} else {
  message("TypeId and LocationType label not usable; using ISO3 + exclusion list ...")
  countries <- loc_df %>%
    mutate(
      iso3_ok = !is.na(ISO3) &
        nchar(str_trim(ISO3)) == 3 &
        str_detect(str_trim(ISO3), "^[A-Za-z]{3}$")
    ) %>%
    filter(
      loc_l != "world",
      iso3_ok,
      !LocationId %in% non_country_ids
    ) %>%
    distinct(LocationId, .keep_all = TRUE) %>%
    arrange(Location)
}

message("Locations kept as countries/areas: ", nrow(countries))
if (nrow(countries) == 0) stop("After filtering, no countries found.")

# Diagnostic: warn if any known aggregates slipped through
suspect <- countries %>% filter(LocationId %in% non_country_ids)
if (nrow(suspect) > 0) {
  message("WARNING: The following known non-country IDs are still in the list (removing them):")
  message("  ", paste(suspect$Location, collapse = ", "))
  countries <- countries %>% filter(!LocationId %in% non_country_ids)
  message("Locations after removing known aggregates: ", nrow(countries))
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

# ---------- Data download helpers ----------
make_data_url <- function(indicator_id, location_id, pageNumber = 1, pageSize = 400) {
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

api_get_all_pages <- function(indicator_id, location_id, pageSize = 400) {
  first <- api_get_json(make_data_url(indicator_id, location_id, pageNumber = 1, pageSize = pageSize))

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(make_data_url(indicator_id, location_id, pageNumber = p, pageSize = pageSize))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

get_indicator_raw <- function(indicator_id, location_id) {
  raw <- tryCatch(
    api_get_all_pages(indicator_id, location_id, pageSize = 400),
    error = function(e) {
      msg <- conditionMessage(e)
      if (grepl("HTTP 404", msg, fixed = TRUE)) {
        message("    -> 404 (no data). Skipping this location.")
        return(tibble())
      }
      stop(e)
    }
  )
  if (nrow(raw) == 0) return(tibble())
  names(raw) <- to_snake(names(raw))
  raw
}

# ---------- Vectorized age-group normalizer (FIX) ----------
normalize_agegrp_0_14 <- function(x) {
  x0 <- str_to_lower(str_trim(as.character(x)))
  x0 <- str_replace_all(x0, "\u2013|\u2014", "-")      # en/em dash -> hyphen
  x0 <- str_replace_all(x0, "\\s+", " ")
  x0 <- str_replace_all(x0, "years|year|yrs|yr", "")
  x0 <- str_replace_all(x0, "\\s+", " ")
  x0 <- str_trim(x0)

  out <- rep(NA_character_, length(x0))
  is_0_14 <- str_detect(x0, "^0\\s*-\\s*14$|^0\\s*to\\s*14$|^0\\s*[-to]+\\s*14$")
  out[is_0_14] <- "0_14"
  out
}

filter_common71_0_14 <- function(df, require_both_sexes = TRUE) {
  sex_any     <- pick1(df, c("sex","sex_label","sexlabel"))
  variant_any <- pick1(df, c("variant","variant_label","variant_short_name","variantshortname"))
  year_any    <- suppressWarnings(as.integer(pick1(df, c("time_label","time","year"))))
  value_any   <- suppressWarnings(as.numeric(pick1(df, c("value"))))

  age_any <- pick1(df, c(
    "age_group","age_group_label","agegrouplabel",
    "age","age_label","agelabel",
    "age_group_short_name","agegroupshortname"
  ))

  out <- tibble(
    Year    = year_any,
    Sex     = sex_any,
    Variant = variant_any,
    AgeRaw  = age_any,
    Value   = value_any
  ) %>%
    filter(!is.na(Year), Year >= start_year, Year <= end_year) %>%
    mutate(
      var_l  = str_to_lower(str_trim(Variant)),
      sex_l  = str_to_lower(str_trim(Sex)),
      AgeGrp = normalize_agegrp_0_14(AgeRaw)
    )

  # Variant filter ONLY if variant exists
  if (!all(is.na(out$var_l))) out <- out %>% filter(var_l %in% c("medium","median"))

  # Both sexes filter ONLY if sex exists
  if (require_both_sexes && !all(is.na(out$sex_l))) out <- out %>% filter(sex_l %in% c("both sexes","both"))

  # Keep ONLY 0-14
  out %>% filter(!is.na(AgeGrp), AgeGrp == "0_14")
}

# ---------- Main loop ----------
checkpoint_csv <- file.path(out_dir, sprintf("WPP_ind71_share_0_14_checkpoint_%d_%d.csv", start_year, end_year))
if (file.exists(checkpoint_csv)) file.remove(checkpoint_csv)

results <- vector("list", nrow(countries))

for (i in seq_len(nrow(countries))) {
  loc_id_i   <- countries$LocationId[i]
  loc_name_i <- countries$Location[i]
  iso2_i     <- countries$ISO2[i]
  iso3_i     <- countries$ISO3[i]

  message(sprintf("[%d/%d] %s (%s) — indicator %d (0-14) ...",
                  i, nrow(countries), loc_name_i, ifelse(is.na(iso3_i), "NA", iso3_i), indicator))

  raw <- get_indicator_raw(indicator, loc_id_i)

  wide_i <- if (nrow(raw) == 0) {
    tibble(Year = start_year:end_year, Share_0_14 = NA_real_)
  } else {
    long <- filter_common71_0_14(raw, require_both_sexes = TRUE) %>%
      group_by(Year) %>%
      summarise(Share_0_14 = mean(Value, na.rm = TRUE), .groups = "drop")

    tibble(Year = start_year:end_year) %>%
      left_join(long, by = "Year") %>%
      arrange(Year)
  }

  panel_i <- wide_i %>%
    mutate(
      LocationId = loc_id_i,
      Location   = loc_name_i,
      ISO2       = iso2_i,
      ISO3       = iso3_i
    ) %>%
    select(LocationId, ISO3, ISO2, Location, Year, Share_0_14)

  results[[i]] <- panel_i

  # ---- Checkpoint append ----
  write.table(
    panel_i,
    file      = checkpoint_csv,
    sep       = ",",
    row.names = FALSE,
    col.names = !file.exists(checkpoint_csv),
    append    = file.exists(checkpoint_csv)
  )
}

final <- bind_rows(results) %>% arrange(Location, Year)

out_csv  <- file.path(out_dir, sprintf("WPP_countries_ind71_share_0_14_%d_%d.csv", start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_countries_ind71_share_0_14_%d_%d.xlsx", start_year, end_year))

write_excel_csv(final, out_csv)
write_xlsx(final, out_xlsx)

message("Saved files:")
message(" - ", out_csv)
message(" - ", out_xlsx)
message("Checkpoint (partial while running):")
message(" - ", checkpoint_csv)
message("Rows: ", nrow(final))
message("Countries: ", n_distinct(final$LocationId))
message("Output folder: ", out_dir)

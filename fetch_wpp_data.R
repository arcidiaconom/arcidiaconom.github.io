# ============================================================
# UN WPP Data Portal API (R) — World series, 1960–2100
# Indicators:
#  - 49: Total population by sex (World, Both sexes ONLY)
#  - 19: Total fertility rate (World; if sex exists -> Both sexes ONLY)
#  - 76: Life expectancy E(x) - complete, x = age 5 (World; Both sexes ONLY)
# Variant: API often labels as "Median" (so we accept medium/median)
# Output: CSV (Excel-friendly) + XLSX
# Resilience: retries on 502/503/504
# Args:
#   arg1 = output folder (e.g., Data_Raw)
#   arg2 = token (optional; used if WPP_TOKEN env var is missing)
# ============================================================

pkgs <- c("httr", "jsonlite", "dplyr", "stringr", "readr", "writexl")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) {
  if (!interactive()) stop("Missing packages: ", paste(to_install, collapse = ", "),
                           ". Install them before running this script.")
  install.packages(to_install)
}

library(httr)
library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(writexl)

# ---- Args ----
args <- commandArgs(trailingOnly = TRUE)

# ---- Token ----
token <- str_trim(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- str_trim(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd argument or set Sys.setenv(WPP_TOKEN='...').")

# ---- Parameters ----
base_url    <- "https://population.un.org/dataportalapi/api/v1"
location_id <- 900   # World
start_year  <- 1960
end_year    <- 2100
page_size   <- 400

# ---- Output folder (from arg1) ----
out_dir <- if (length(args) >= 1 && nzchar(args[1])) args[1] else getwd()
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = FALSE)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# ---- Helpers ----
to_snake <- function(x) {
  x <- gsub("([a-z0-9])([A-Z])", "\\1_\\2", x)
  tolower(x)
}

api_get_json <- function(url, max_tries = 6) {
  for (i in 1:max_tries) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))

    if (!http_error(r)) {
      return(fromJSON(content(r, as = "text", encoding = "UTF-8"), flatten = TRUE))
    }

    code <- status_code(r)
    body <- content(r, as = "text", encoding = "UTF-8")

    if (code %in% c(502, 503, 504)) {
      wait <- 2^(i - 1)
      message("HTTP ", code, " (try ", i, "/", max_tries, "). Waiting ", wait, "s then retrying...")
      Sys.sleep(wait)
      next
    }

    stop("HTTP ", code, " for:\n", url, "\n\n", body)
  }

  stop("Failed after ", max_tries, " tries for:\n", url)
}

make_url <- function(indicator_id, pageNumber = 1) {
  paste0(
    base_url,
    "/data/indicators/", indicator_id,
    "/locations/", location_id,
    "/start/", start_year,
    "/end/", end_year,
    "/?format=json",
    "&pageNumber=", pageNumber,
    "&pageSize=", page_size
  )
}

api_get_all_pages <- function(indicator_id) {
  first <- api_get_json(make_url(indicator_id, pageNumber = 1))

  out <- list()
  if (!is.null(first$data) && NROW(first$data) > 0) out[[1]] <- first$data

  pages <- first$pages
  if (!is.null(pages) && pages > 1) {
    for (p in 2:pages) {
      res <- api_get_json(make_url(indicator_id, pageNumber = p))
      if (!is.null(res$data) && NROW(res$data) > 0) out[[length(out) + 1]] <- res$data
    }
  }

  if (length(out) == 0) tibble() else bind_rows(out)
}

pick1 <- function(df, candidates) {
  candidates <- candidates[candidates %in% names(df)]
  if (length(candidates) == 0) stop("None of these columns found: ", paste(candidates, collapse = ", "))
  df[[candidates[1]]]
}

get_indicator_raw <- function(indicator_id) {
  message("Downloading indicator ", indicator_id, " ...")
  raw <- api_get_all_pages(indicator_id)
  if (nrow(raw) == 0) stop("No data returned for indicator ", indicator_id)
  names(raw) <- to_snake(names(raw))
  raw
}

filter_common <- function(df, require_both_sexes = FALSE, extra_cols = NULL) {
  sex_any     <- pick1(df, c("sex", "sex_label", "sexlabel"))
  variant_any <- pick1(df, c("variant", "variant_label", "variant_short_name", "variantshortname"))
  year_any    <- suppressWarnings(as.integer(pick1(df, c("time_label", "time", "year"))))
  value_any   <- suppressWarnings(as.numeric(pick1(df, c("value"))))

  out <- tibble(
    Year    = year_any,
    Sex     = sex_any,
    Variant = variant_any,
    Value   = value_any
  )

  # Attach any extra columns requested by the caller
  if (!is.null(extra_cols)) {
    for (col in names(extra_cols)) {
      out[[col]] <- pick1(df, extra_cols[[col]])
    }
  }

  out <- out %>%
    filter(!is.na(Year), Year >= start_year, Year <= end_year) %>%
    mutate(
      var_l = str_to_lower(str_trim(Variant)),
      sex_l = str_to_lower(str_trim(Sex))
    ) %>%
    filter(var_l %in% c("medium", "median"))

  if (require_both_sexes && any(!is.na(out$Sex))) {
    out <- out %>% filter(sex_l %in% c("both sexes", "both"))
  }

  out
}

# ============================================================
# 49: Total population (Both sexes)
# ============================================================
raw49 <- get_indicator_raw(49)
pop49 <- filter_common(raw49, require_both_sexes = TRUE) %>%
  transmute(Year, Total_Population = Value) %>%
  distinct()

# ============================================================
# 19: Total fertility rate (Both sexes if sex exists)
# ============================================================
raw19 <- get_indicator_raw(19)
tfr19 <- filter_common(raw19, require_both_sexes = TRUE) %>%
  transmute(Year, Total_Fertility_Rate = Value) %>%
  distinct()

# ============================================================
# 76: Life expectancy E(x) - complete, x = age 5 (Both sexes)
# ============================================================
raw76 <- get_indicator_raw(76)

age_extra_cols <- list(
  age_start = c("age_start", "agestart"),
  age_end   = c("age_end", "ageend"),
  age_mid   = c("age_mid", "agemid"),
  age_label = c("age_label", "agelabel")
)

df76 <- filter_common(raw76, require_both_sexes = TRUE, extra_cols = age_extra_cols) %>%
  mutate(
    age_start   = suppressWarnings(as.integer(age_start)),
    age_end     = suppressWarnings(as.integer(age_end)),
    age_mid     = suppressWarnings(as.integer(age_mid)),
    age_label_l = str_to_lower(str_trim(age_label))
  )

le76_age5 <- df76 %>%
  filter(
    (!is.na(age_start) & !is.na(age_end) & age_start == 5 & age_end == 5) |
      (!is.na(age_mid) & age_mid == 5) |
      (is.na(age_start) & is.na(age_mid) & str_detect(age_label_l, "^5$|age\\s*5"))
  ) %>%
  transmute(Year, Life_Expectancy_Age5 = Value) %>%
  distinct()

if (nrow(le76_age5) == 0) {
  stop(
    "Indicator 76: after filtering to age 5, got 0 rows.\n",
    "Inspect unique age labels via: unique(df76$age_label)"
  )
}

# ============================================================
# Merge and export
# ============================================================
final <- pop49 %>%
  full_join(tfr19, by = "Year") %>%
  full_join(le76_age5, by = "Year") %>%
  arrange(Year)

out_csv  <- file.path(out_dir, sprintf("WPP_world_%d_%d.csv", start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_world_%d_%d.xlsx", start_year, end_year))

write_excel_csv(final, out_csv)
write_xlsx(final, out_xlsx)

message("Saved files:")
message(" - ", out_csv)
message(" - ", out_xlsx)
message("Rows: ", nrow(final), " (expected ", end_year - start_year + 1, ")")
message("Output folder: ", out_dir)

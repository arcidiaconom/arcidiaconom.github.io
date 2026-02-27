# ============================================================
# UN WPP Data Portal API (R) — World series, 1960–2100
# Indicators:
#  - 49: Total population (Both sexes)
#  - 19: Total fertility rate (Both sexes)
#  - 76: Life expectancy E(x) at age 5 (Both sexes)
# Variant: medium/median
# Output: CSV (Excel-friendly) + XLSX
# Args:
#   arg1 = output folder (default: working directory)
#   arg2 = API token (fallback if WPP_TOKEN env var is unset)
# ============================================================

pkgs <- c("httr", "jsonlite", "dplyr", "stringr", "readr", "writexl")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) {
  if (!interactive()) stop("Missing packages: ", paste(to_install, collapse = ", "))
  install.packages(to_install)
}

library(httr)
library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(writexl)

args <- commandArgs(trailingOnly = TRUE)

# Token: env var first, then CLI arg
token <- str_trim(Sys.getenv("WPP_TOKEN", unset = ""))
if (!nzchar(token) && length(args) >= 2) token <- str_trim(args[2])
if (!nzchar(token)) stop("Missing token. Pass as 2nd arg or set WPP_TOKEN env var.")

# Parameters
base_url    <- "https://population.un.org/dataportalapi/api/v1"
location_id <- 900   # World
start_year  <- 1960
end_year    <- 2100
page_size   <- 400

# Output folder
out_dir <- if (length(args) >= 1 && nzchar(args[1])) args[1] else getwd()
out_dir <- normalizePath(out_dir, winslash = "/", mustWork = FALSE)
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# ---- Helpers ----

to_snake <- function(x) tolower(gsub("([a-z0-9])([A-Z])", "\\1_\\2", x))

pick1 <- function(df, candidates) {
  found <- intersect(candidates, names(df))
  if (length(found) == 0) stop("Column not found. Tried: ", paste(candidates, collapse = ", "))
  df[[found[1]]]
}

api_get_json <- function(url, max_tries = 6) {
  for (i in seq_len(max_tries)) {
    r <- GET(url, add_headers(Authorization = paste0("Bearer ", token)))
    if (!http_error(r))
      return(fromJSON(content(r, "text", encoding = "UTF-8"), flatten = TRUE))

    code <- status_code(r)
    if (code %in% c(502, 503, 504)) {
      wait <- 2^(i - 1)
      message("HTTP ", code, " (try ", i, "/", max_tries, "). Retrying in ", wait, "s...")
      Sys.sleep(wait)
      next
    }
    stop("HTTP ", code, " for:\n", url, "\n\n", content(r, "text", encoding = "UTF-8"))
  }
  stop("Failed after ", max_tries, " tries for:\n", url)
}

api_get_all_pages <- function(indicator_id) {
  make_url <- function(page) {
    paste0(base_url, "/data/indicators/", indicator_id,
           "/locations/", location_id,
           "/start/", start_year, "/end/", end_year,
           "/?format=json&pageNumber=", page, "&pageSize=", page_size)
  }

  first <- api_get_json(make_url(1))
  pages <- first$pages %||% 1
  results <- list(first$data)

  for (p in seq_len(pages)[-1]) {
    results[[p]] <- api_get_json(make_url(p))$data
  }

  bind_rows(results)
}

get_indicator <- function(indicator_id) {
  message("Downloading indicator ", indicator_id, " ...")
  raw <- api_get_all_pages(indicator_id)
  if (nrow(raw) == 0) stop("No data returned for indicator ", indicator_id)
  names(raw) <- to_snake(names(raw))
  raw
}

filter_common <- function(df, both_sexes = FALSE, extra_cols = NULL) {
  out <- tibble(
    Year    = suppressWarnings(as.integer(pick1(df, c("time_label", "time", "year")))),
    Sex     = pick1(df, c("sex", "sex_label", "sexlabel")),
    Variant = pick1(df, c("variant", "variant_label", "variant_short_name", "variantshortname")),
    Value   = suppressWarnings(as.numeric(pick1(df, c("value"))))
  )

  for (col in names(extra_cols)) out[[col]] <- pick1(df, extra_cols[[col]])

  out <- out %>%
    filter(!is.na(Year), between(Year, start_year, end_year),
           str_to_lower(str_trim(Variant)) %in% c("medium", "median"))

  if (both_sexes && any(!is.na(out$Sex))) {
    out <- filter(out, str_to_lower(str_trim(Sex)) %in% c("both sexes", "both"))
  }

  select(out, -Sex, -Variant)
}

# ---- 49: Total population ----
pop <- get_indicator(49) %>%
  filter_common(both_sexes = TRUE) %>%
  transmute(Year, Total_Population = Value) %>%
  distinct()

# ---- 19: Total fertility rate ----
tfr <- get_indicator(19) %>%
  filter_common(both_sexes = TRUE) %>%
  transmute(Year, Total_Fertility_Rate = Value) %>%
  distinct()

# ---- 76: Life expectancy at age 5 ----
le_raw <- get_indicator(76) %>%
  filter_common(both_sexes = TRUE, extra_cols = list(
    age_start = c("age_start", "agestart"),
    age_end   = c("age_end", "ageend"),
    age_mid   = c("age_mid", "agemid"),
    age_label = c("age_label", "agelabel")
  )) %>%
  mutate(across(c(age_start, age_end, age_mid), ~ suppressWarnings(as.integer(.x))),
         age_label_l = str_to_lower(str_trim(age_label)))

le <- le_raw %>%
  filter(
    (!is.na(age_start) & !is.na(age_end) & age_start == 5 & age_end == 5) |
      (!is.na(age_mid) & age_mid == 5) |
      (is.na(age_start) & is.na(age_mid) & str_detect(age_label_l, "^5$|age\\s*5"))
  ) %>%
  transmute(Year, Life_Expectancy_Age5 = Value) %>%
  distinct()

if (nrow(le) == 0) {
  stop("Indicator 76: 0 rows after age-5 filter.\n",
       "Check: unique(le_raw$age_label)")
}

# ---- Merge and export ----
final <- pop %>%
  full_join(tfr, by = "Year") %>%
  full_join(le, by = "Year") %>%
  arrange(Year)

out_csv  <- file.path(out_dir, sprintf("WPP_world_%d_%d.csv",  start_year, end_year))
out_xlsx <- file.path(out_dir, sprintf("WPP_world_%d_%d.xlsx", start_year, end_year))

write_excel_csv(final, out_csv)
write_xlsx(final, out_xlsx)

message("Saved: ", out_csv, "\n       ", out_xlsx)
message("Rows: ", nrow(final), " (expected ", end_year - start_year + 1, ")")

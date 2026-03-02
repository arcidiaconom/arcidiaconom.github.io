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
#   - Keeps years 1990, 2020, and 2050
#   - Saves:
#       wb_population_5yr_by_sex_1990_2020_2050.csv
#       wb_population_5yr_by_sex_1990_2020_2050.xlsx
# ============================================================

# --- Install missing packages automatically ---
required_pkgs <- c("wbstats", "dplyr", "openxlsx")
missing_pkgs  <- required_pkgs[!vapply(required_pkgs, requireNamespace,
                                        quietly = TRUE, FUN.VALUE = logical(1))]
if (length(missing_pkgs) > 0) {
  message("Installing missing packages: ", paste(missing_pkgs, collapse = ", "))
  install.packages(missing_pkgs, repos = "https://cloud.r-project.org")
}

suppressPackageStartupMessages({
  library(wbstats)
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

message("Downloading ", length(indicators), " indicators from World Bank API ...")

df <- wb_data(
  indicator   = indicators,
  country     = "countries_only",
  start_date  = 1990,
  end_date    = 2050,
  return_wide = FALSE
) %>%
  filter(date %in% c(1990, 2020, 2050)) %>%
  mutate(
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
    iso3c, country, date,
    indicator_id, age_code, age_group, sex,
    value, unit, obs_status, footnote, last_updated
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

/*==============================================================================
  UN World Population Prospects 2024 — Import & Clean

  Source page (Standard Projections > Population):
    https://population.un.org/wpp/downloads?folder=Standard%20Projections&group=Population

  File: "Population by Select Age Groups – Both Sexes"
    WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx

  Replicates the following pandas call:
    df = pd.read_excel(
      "https://population.un.org/wpp/assets/Excel Files/1_Indicator (Standard)/"
      "EXCEL_FILES/2_Population/"
      "WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx",
      sheet_name="Estimates",
      skiprows=16,
    )
==============================================================================*/

clear all
set more off

* --------------------------------------------------------------------------- *
* 1. Download the Excel file from the UN Population Division
*    Browse the file list at:
*    https://population.un.org/wpp/downloads?folder=Standard%20Projections&group=Population
*
*    If the URL below stops working, try the alternative path shown after it,
*    or download manually from the page above.
* --------------------------------------------------------------------------- *

local filename "WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx"

* Primary URL (matches the original pandas code)
local url "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/EXCEL_FILES/2_Population/`filename'"

* Alternative URL (newer path used on the 2024 site)
* local url "https://population.un.org/wpp/Download/Files/1_Indicator%20(Standard)/EXCEL_FILES/2_Population/`filename'"

copy "`url'" "`filename'", replace

* --------------------------------------------------------------------------- *
* 2. Import the "Estimates" sheet, skipping the first 16 rows
* --------------------------------------------------------------------------- *

import excel "`filename'", ///
    sheet("Estimates") cellrange(A17) firstrow clear

* --------------------------------------------------------------------------- *
* 3. Basic cleaning
* --------------------------------------------------------------------------- *

* Destring numeric columns that may have been read as strings
quietly ds, has(type string)
foreach var of varlist `r(varlist)' {
    capture destring `var', replace
}

compress

* --------------------------------------------------------------------------- *
* 4. Quick look at the data
* --------------------------------------------------------------------------- *

describe
summarize
list in 1/5

* --------------------------------------------------------------------------- *
* 5. (Optional) Save as a Stata dataset
* --------------------------------------------------------------------------- *

save "un_population_estimates.dta", replace

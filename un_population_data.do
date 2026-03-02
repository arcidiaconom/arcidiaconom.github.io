/*==============================================================================
  UN World Population Prospects 2024 — Import & Clean

  Replicates in Stata:
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
* --------------------------------------------------------------------------- *

local url "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/EXCEL_FILES/2_Population/WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx"

copy "`url'" "WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx", replace

* --------------------------------------------------------------------------- *
* 2. Import the "Estimates" sheet, skipping the first 16 rows
* --------------------------------------------------------------------------- *

import excel "WPP2024_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx", ///
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

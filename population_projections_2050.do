/*==============================================================================
  Population Estimates and Projections - World Bank

  Downloads all 5-year age group population indicators by gender for 2050
  Indicators follow the pattern: SP.POP.XXYY.MA / SP.POP.XXYY.FE

  Requires: wbopendata (install via: ssc install wbopendata)
==============================================================================*/

clear all
set more off

*-------------------------------------------------------------------------------
* Define indicator lists
*-------------------------------------------------------------------------------

* Male indicators (MA)
local male_indicators ///
    SP.POP.0004.MA ///
    SP.POP.0509.MA ///
    SP.POP.1014.MA ///
    SP.POP.1519.MA ///
    SP.POP.2024.MA ///
    SP.POP.2529.MA ///
    SP.POP.3034.MA ///
    SP.POP.3539.MA ///
    SP.POP.4044.MA ///
    SP.POP.4549.MA ///
    SP.POP.5054.MA ///
    SP.POP.5559.MA ///
    SP.POP.6064.MA ///
    SP.POP.6569.MA ///
    SP.POP.7074.MA ///
    SP.POP.7579.MA ///
    SP.POP.80UP.MA

* Female indicators (FE)
local female_indicators ///
    SP.POP.0004.FE ///
    SP.POP.0509.FE ///
    SP.POP.1014.FE ///
    SP.POP.1519.FE ///
    SP.POP.2024.FE ///
    SP.POP.2529.FE ///
    SP.POP.3034.FE ///
    SP.POP.3539.FE ///
    SP.POP.4044.FE ///
    SP.POP.4549.FE ///
    SP.POP.5054.FE ///
    SP.POP.5559.FE ///
    SP.POP.6064.FE ///
    SP.POP.6569.FE ///
    SP.POP.7074.FE ///
    SP.POP.7579.FE ///
    SP.POP.80UP.FE

*-------------------------------------------------------------------------------
* Download male population data for 2050
*-------------------------------------------------------------------------------

local first = 1

foreach ind of local male_indicators {

    * wbopendata converts dots to underscores and lowercases variable names
    local varname = lower(subinstr("`ind'", ".", "_", .))

    wbopendata, indicator(`ind') year(2050) clear long

    * Keep only relevant variables
    keep countrycode countryname year `varname'
    rename `varname' pop_value

    * Extract age group from indicator name
    local age_part = subinstr("`ind'", "SP.POP.", "", 1)
    local age_part = subinstr("`age_part'", ".MA", "", 1)
    gen age_group = "`age_part'"
    gen gender = "Male"
    gen indicator = "`ind'"

    if `first' {
        tempfile combined
        save `combined', replace
        local first = 0
    }
    else {
        append using `combined'
        save `combined', replace
    }
}

*-------------------------------------------------------------------------------
* Download female population data for 2050
*-------------------------------------------------------------------------------

foreach ind of local female_indicators {

    local varname = lower(subinstr("`ind'", ".", "_", .))

    wbopendata, indicator(`ind') year(2050) clear long

    keep countrycode countryname year `varname'
    rename `varname' pop_value

    local age_part = subinstr("`ind'", "SP.POP.", "", 1)
    local age_part = subinstr("`age_part'", ".FE", "", 1)
    gen age_group = "`age_part'"
    gen gender = "Female"
    gen indicator = "`ind'"

    append using `combined'
    save `combined', replace
}

*-------------------------------------------------------------------------------
* Clean and label the data
*-------------------------------------------------------------------------------

* Create readable age group labels
gen age_label = ""
replace age_label = "0-4"   if age_group == "0004"
replace age_label = "5-9"   if age_group == "0509"
replace age_label = "10-14" if age_group == "1014"
replace age_label = "15-19" if age_group == "1519"
replace age_label = "20-24" if age_group == "2024"
replace age_label = "25-29" if age_group == "2529"
replace age_label = "30-34" if age_group == "3034"
replace age_label = "35-39" if age_group == "3539"
replace age_label = "40-44" if age_group == "4044"
replace age_label = "45-49" if age_group == "4549"
replace age_label = "50-54" if age_group == "5054"
replace age_label = "55-59" if age_group == "5559"
replace age_label = "60-64" if age_group == "6064"
replace age_label = "65-69" if age_group == "6569"
replace age_label = "70-74" if age_group == "7074"
replace age_label = "75-79" if age_group == "7579"
replace age_label = "80+"   if age_group == "80UP"

* Create numeric age order variable for sorting
gen age_order = .
replace age_order = 1  if age_group == "0004"
replace age_order = 2  if age_group == "0509"
replace age_order = 3  if age_group == "1014"
replace age_order = 4  if age_group == "1519"
replace age_order = 5  if age_group == "2024"
replace age_order = 6  if age_group == "2529"
replace age_order = 7  if age_group == "3034"
replace age_order = 8  if age_group == "3539"
replace age_order = 9  if age_group == "4044"
replace age_order = 10 if age_group == "4549"
replace age_order = 11 if age_group == "5054"
replace age_order = 12 if age_group == "5559"
replace age_order = 13 if age_group == "6064"
replace age_order = 14 if age_group == "6569"
replace age_order = 15 if age_group == "7074"
replace age_order = 16 if age_group == "7579"
replace age_order = 17 if age_group == "80UP"

* Sort and order variables
sort countrycode gender age_order
order countrycode countryname year gender age_label age_group indicator pop_value

* Label variables
label variable countrycode  "Country Code (ISO3)"
label variable countryname  "Country Name"
label variable year          "Year"
label variable gender        "Gender"
label variable age_label     "Age Group"
label variable age_group     "Age Group Code"
label variable indicator     "World Bank Indicator Code"
label variable pop_value     "Population"
label variable age_order     "Age Group Sort Order"

* Drop rows with missing population values
drop if missing(pop_value)

*-------------------------------------------------------------------------------
* Save output
*-------------------------------------------------------------------------------

* Save as Stata dataset
save "population_by_age_gender_2050.dta", replace

* Also export to CSV for convenience
export delimited using "population_by_age_gender_2050.csv", replace

display as text _n "======================================================"
display as text "Download complete."
display as text "  Observations: " _N
display as text "  Output files:"
display as text "    - population_by_age_gender_2050.dta"
display as text "    - population_by_age_gender_2050.csv"
display as text "======================================================"

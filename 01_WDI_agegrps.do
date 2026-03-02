/*==============================================================================
  Download World Bank "Population estimates and projections" data
  for all 5-year age groups by gender for years 1990, 2020, and 2050.

  Indicators follow the pattern: SP.POP.<age_code>.<gender>
    e.g. SP.POP.3539.MA = Male population aged 35-39

  Source 40 = "Health Nutrition and Population Statistics:
               Population estimates and projections"

  Called by:  RUN ALL.do  (expects ${data_raw} to be set)

  Output:
      ${data_raw}/population_projections.csv
      ${data_raw}/population_projections.dta

  Requirements: Stata 14+ (uses filefilter and copy with URLs)
==============================================================================*/

*-------------------------------------------------------------------------------
* Configuration
*-------------------------------------------------------------------------------
local years      1990 2020 2050
local per_page   500
local base_url   "https://api.worldbank.org/v2"
local max_retries 3

local outcsv  "${data_raw}/population_projections.csv"
local outdta  "${data_raw}/population_projections.dta"

*-------------------------------------------------------------------------------
* Define age groups and gender codes
*-------------------------------------------------------------------------------
local age_codes   "0004" "0509" "1014" "1519" "2024" "2529" "3034" "3539" ///
                  "4044" "4549" "5054" "5559" "6064" "6569" "7074" "7579" "80UP"
local age_labels  "0-4"  "5-9"  "10-14" "15-19" "20-24" "25-29" "30-34" "35-39" ///
                  "40-44" "45-49" "50-54" "55-59" "60-64" "65-69" "70-74" "75-79" "80+"

local gender_codes   "MA" "FE"
local gender_labels  "Male" "Female"

*-------------------------------------------------------------------------------
* Count total indicators (for progress display)
*-------------------------------------------------------------------------------
local n_age     : word count `age_codes'
local n_gender  : word count `gender_codes'
local n_indicators = `n_age' * `n_gender'

display as text "Will download `n_indicators' indicators per year"

*-------------------------------------------------------------------------------
* Create empty master dataset
*-------------------------------------------------------------------------------
tempfile master
clear
gen str3    country_code = ""
gen str100  country_name = ""
gen str30   indicator    = ""
gen str10   age_group    = ""
gen str10   gender       = ""
gen int     year         = .
gen double  value        = .
save `master', replace

*-------------------------------------------------------------------------------
* Loop over years, age groups, and genders — fetch from World Bank API
*-------------------------------------------------------------------------------
local total_records = 0

foreach yr of local years {

    display as text _newline
    display as text "=========================================="
    display as text " Year `yr': downloading `n_indicators' indicators"
    display as text "=========================================="
    display as text ""

    local i = 0
    local a = 0

    foreach acode of local age_codes {
        local ++a
        local alabel : word `a' of `age_labels'

        local g = 0

        foreach gcode of local gender_codes {
            local ++g
            local glabel : word `g' of `gender_labels'
            local ++i

            local ind "SP.POP.`acode'.`gcode'"

            display as text "[`i'/`n_indicators'] `ind' (`alabel', `glabel') ..."

            local page        = 1
            local total_pages = 1
            local rec_count   = 0

            while `page' <= `total_pages' {

                local url "`base_url'/country/all/indicator/`ind'?date=`yr'&source=40&format=json&per_page=`per_page'&page=`page'"

                *--- Download JSON with retry ---
                local success = 0
                forvalues attempt = 1/`max_retries' {
                    tempfile jsonfile
                    capture copy "`url'" `jsonfile', replace
                    if _rc == 0 {
                        local success = 1
                        continue, break
                    }
                    display as text "    retry `attempt'/`max_retries' (rc=`=_rc') ..."
                    sleep 2000
                }

                if `success' == 0 {
                    display as error "    FAILED after `max_retries' retries — skipping"
                    continue, break
                }

                *--- Split JSON records onto separate lines ---
                tempfile splitfile
                filefilter `jsonfile' `splitfile', from("},{") to("}\r\n{") replace

                *--- Read each line as one observation ---
                clear
                infix str4000 v1 1-4000 using `splitfile', clear

                *--- Extract pagination from first page ---
                if `page' == 1 {
                    gen _pg = regexs(1) if regexm(v1, `""pages":([0-9]+)"')
                    local total_pages = _pg[1]
                    if "`total_pages'" == "" | "`total_pages'" == "." {
                        local total_pages = 1
                    }
                    drop _pg
                }

                *--- Parse fields ---
                gen country_code = regexs(1) if regexm(v1, `""countryiso3code":"([^"]+)"')
                gen country_name = regexs(1) if regexm(v1, `""country":[^}]*"value":"([^"]+)"')
                gen value_str    = regexs(1) if regexm(v1, `""value":([0-9][0-9.eE+-]*)"')
                gen double value = real(value_str)

                *--- Keep valid country records only ---
                drop if missing(country_code) | country_code == ""
                drop v1 value_str

                *--- Attach metadata ---
                gen str30 indicator = "`ind'"
                gen str10 age_group = "`alabel'"
                gen str10 gender    = "`glabel'"
                gen int   year      = `yr'

                order country_code country_name indicator age_group gender year value

                local rec_count = `rec_count' + _N

                *--- Append to master ---
                append using `master'
                save `master', replace

                local ++page
                sleep 500
            }

            local total_records = `total_records' + `rec_count'
            display as text "    -> `rec_count' records"

            * Pause between indicators to avoid rate-limiting
            sleep 1000
        }
    }
}

*-------------------------------------------------------------------------------
* Final dataset
*-------------------------------------------------------------------------------
use `master', clear
drop if country_code == "" & country_name == ""

sort country_code year age_group gender

label variable country_code "ISO3 country code"
label variable country_name "Country name"
label variable indicator    "World Bank indicator code"
label variable age_group    "5-year age group"
label variable gender       "Gender (Male/Female)"
label variable year         "Year"
label variable value        "Population"

compress

export delimited using "`outcsv'", replace
display as text _newline "Saved CSV:  `outcsv'"

save "`outdta'", replace
display as text "Saved DTA:  `outdta'"

display as text _newline "Total observations: `=_N'"
display as text "Total records fetched: `total_records'"
display as text "Done."

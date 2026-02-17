/*==============================================================================
  Download World Bank "Population estimates and projections" data
  for all 5-year age groups by gender for year 2050.

  Indicators follow the pattern: SP.POP.<age_code>.<gender>
    e.g. SP.POP.3539.MA = Male population aged 35-39

  Usage:
      do download_population_projections.do
      -- OR set the global macro output_dir before running --
      global output_dir "C:/my/output/folder"
      do download_population_projections.do

  Output:
      <output_dir>/population_projections_2050.csv
      <output_dir>/population_projections_2050.dta

  Requirements:
      Stata 14+
==============================================================================*/

clear all
set more off

*-------------------------------------------------------------------------------
* Configuration
*-------------------------------------------------------------------------------
local year      2050
local per_page  500
local base_url  "https://api.worldbank.org/v2"

* Output directory: use global if set, otherwise current directory
if "${output_dir}" != "" {
    local outdir "${output_dir}"
}
else {
    local outdir "."
}

capture mkdir "`outdir'"

local outcsv  "`outdir'/population_projections_2050.csv"
local outdta  "`outdir'/population_projections_2050.dta"

*-------------------------------------------------------------------------------
* Define age groups and gender codes
*-------------------------------------------------------------------------------
local age_codes   `" "0004" "0509" "1014" "1519" "2024" "2529" "3034" "3539" "4044" "4549" "5054" "5559" "6064" "6569" "7074" "7579" "80UP" "'
local age_labels  `" "0-4" "5-9" "10-14" "15-19" "20-24" "25-29" "30-34" "35-39" "40-44" "45-49" "50-54" "55-59" "60-64" "65-69" "70-74" "75-79" "80+" "'

local gender_codes  `" "MA" "FE" "'
local gender_labels `" "Male" "Female" "'

*-------------------------------------------------------------------------------
* Build indicator list
*-------------------------------------------------------------------------------
local indicators ""
local ind_age_labels ""
local ind_gender_labels ""
local n_indicators 0

local a = 0
foreach acode of local age_codes {
    local a = `a' + 1
    local alabel : word `a' of `age_labels'

    local g = 0
    foreach gcode of local gender_codes {
        local g = `g' + 1
        local glabel : word `g' of `gender_labels'

        local indicator "SP.POP.`acode'.`gcode'"
        local n_indicators = `n_indicators' + 1

        local indicators        `"`indicators' "`indicator'""'
        local ind_age_labels    `"`ind_age_labels' "`alabel'""'
        local ind_gender_labels `"`ind_gender_labels' "`glabel'""'
    }
}

display as text "Downloading `n_indicators' indicators for year `year'..."
display as text "Output: `outcsv'"
display as text ""

*-------------------------------------------------------------------------------
* Create empty master dataset to accumulate results
*-------------------------------------------------------------------------------
tempfile master
clear
gen str3   country_code = ""
gen str100 country_name = ""
gen str30  indicator    = ""
gen str10  age_group    = ""
gen str10  gender       = ""
gen int    year         = .
gen double value        = .
save `master', replace

*-------------------------------------------------------------------------------
* Loop over all indicators and fetch data from World Bank API
*
* KEY DESIGN: We never store raw JSON in Stata local macros (which would
* break on special characters like : { } ").  Instead we:
*   1. Download JSON to a temp file
*   2. Use filefilter to split records onto separate lines (file-level)
*   3. Import lines as string variable observations
*   4. Parse fields with regexm() on variables — no macro involvement
*-------------------------------------------------------------------------------
local i = 0
foreach ind of local indicators {
    local i = `i' + 1
    local alabel  : word `i' of `ind_age_labels'
    local glabel  : word `i' of `ind_gender_labels'

    display as text "[`i'/`n_indicators'] Fetching `ind' (ages `alabel', `glabel')..."

    local page = 1
    local total_pages = 1
    local rec_count = 0

    while `page' <= `total_pages' {

        local url "`base_url'/country/all/indicator/`ind'?date=`year'&source=40&format=json&per_page=`per_page'&page=`page'"

        * --- Step 1: Download JSON to a temp file ---
        tempfile jsonfile
        capture copy "`url'" `jsonfile', replace

        if _rc != 0 {
            display as error "  Error fetching `ind' page `page' (rc = " _rc ")"
            continue, break
        }

        * --- Step 2: Split JSON records onto separate lines ---
        * The pattern },{ only appears between top-level array elements,
        * so replacing it with }\n{ puts each record on its own line.
        tempfile splitfile
        filefilter `jsonfile' `splitfile', from("},{") to("}\r\n{") replace

        * --- Step 3: Import each line as one string observation ---
        * Use infix (not import delimited) to avoid quote-parsing and
        * option-compatibility issues across Stata versions.
        clear
        infix str2045 v1 1-2045 using `splitfile', clear

        * --- Step 4a: Extract pagination metadata (variable-level, no macros) ---
        if `page' == 1 {
            * The first observation contains the metadata header with "pages":N
            gen _pg = regexs(1) if regexm(v1, `""pages":([0-9]+)"')
            local total_pages = _pg[1]
            if "`total_pages'" == "" | "`total_pages'" == "." {
                local total_pages = 1
            }
            drop _pg
        }

        * --- Step 4b: Parse country data using regexm on variables ---
        * countryiso3code
        gen country_code = regexs(1) if regexm(v1, `""countryiso3code":"([^"]+)"')

        * Country name: inside "country":{"id":"...","value":"<name>"}
        gen country_name = regexs(1) if regexm(v1, `""country":[^}]*"value":"([^"]+)"')

        * Numeric value: "value":1234.56  (string values like "value":"text" won't match)
        gen value_str = regexs(1) if regexm(v1, `""value":([0-9][0-9.eE+-]*)"')
        gen double value = real(value_str)

        * --- Step 5: Keep only valid country records ---
        drop if missing(country_code) | country_code == ""
        drop v1 value_str

        * --- Step 6: Add indicator metadata ---
        gen str30 indicator = "`ind'"
        gen str10 age_group = "`alabel'"
        gen str10 gender    = "`glabel'"
        gen int   year      = `year'

        order country_code country_name indicator age_group gender year value

        local rec_count = `rec_count' + _N

        * --- Step 7: Append to master ---
        append using `master'
        save `master', replace

        local page = `page' + 1

        * Be polite to the API
        sleep 500
    }

    display as text "  -> `rec_count' records"
}

*-------------------------------------------------------------------------------
* Final dataset: clean up and export
*-------------------------------------------------------------------------------
use `master', clear

* Drop empty seed observations
drop if country_code == "" & country_name == ""

* Sort
sort country_code age_group gender

* Label variables
label variable country_code "ISO3 country code"
label variable country_name "Country name"
label variable indicator    "World Bank indicator code"
label variable age_group    "5-year age group"
label variable gender       "Gender (Male/Female)"
label variable year         "Projection year"
label variable value        "Projected population"

* Export CSV
export delimited using "`outcsv'", replace
display as text ""
display as text "Wrote CSV: `outcsv'"

* Save Stata .dta
compress
save "`outdta'", replace
display as text "Wrote DTA: `outdta'"

display as text ""
display as text "Done! Total observations: " _N

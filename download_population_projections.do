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
      Stata 14+ (uses copy for URL downloads and tempfiles)
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
* Age group codes and labels
local age_codes   `" "0004" "0509" "1014" "1519" "2024" "2529" "3034" "3539" "4044" "4549" "5054" "5559" "6064" "6569" "7074" "7579" "80UP" "'
local age_labels  `" "0-4" "5-9" "10-14" "15-19" "20-24" "25-29" "30-34" "35-39" "40-44" "45-49" "50-54" "55-59" "60-64" "65-69" "70-74" "75-79" "80+" "'

* Gender codes and labels
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

        local indicators       `"`indicators' "`indicator'""'
        local ind_age_labels   `"`ind_age_labels' "`alabel'""'
        local ind_gender_labels `"`ind_gender_labels' "`glabel'""'
    }
}

display as text "Downloading `n_indicators' indicators for year `year'..."
display as text "Output: `outcsv'"
display as text ""

*-------------------------------------------------------------------------------
* Create empty dataset to accumulate results
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
*-------------------------------------------------------------------------------
local i = 0
foreach ind of local indicators {
    local i = `i' + 1
    local alabel  : word `i' of `ind_age_labels'
    local glabel  : word `i' of `ind_gender_labels'

    display as text "[`i'/`n_indicators'] Fetching `ind' (ages `alabel', `glabel')..."

    * Paginate through results
    local page = 1
    local total_pages = 1
    local rec_count = 0

    while `page' <= `total_pages' {

        local url "`base_url'/country/all/indicator/`ind'?date=`year'&format=json&per_page=`per_page'&page=`page'"

        * Download JSON to a temp file
        tempfile jsonfile
        capture copy "`url'" `jsonfile', replace

        if _rc != 0 {
            display as error "  Error fetching `ind' page `page' (rc = " _rc ")"
            continue, break
        }

        * Read the JSON as a text file
        tempfile parsed
        clear
        gen strL raw_json = ""
        set obs 1
        replace raw_json = fileread(`jsonfile')

        * ---------------------------------------------------------------
        * Parse total pages from the metadata header (first occurrence)
        * The JSON looks like: [{"page":1,"pages":3,...},[{...},{...},...]]
        * ---------------------------------------------------------------
        if `page' == 1 {
            * Extract "pages": value from metadata
            local raw_content = raw_json[1]
            local pages_pos = strpos(`"`raw_content'"', `""pages":"')
            if `pages_pos' == 0 {
                local pages_pos = strpos(`"`raw_content'"', `""pages":"')
            }

            * Use regex to extract pages count
            gen str1000 meta_chunk = substr(raw_json, 1, 200)
            gen pages_str = regexs(1) if regexm(meta_chunk, `""pages":([0-9]+)"')
            local total_pages = pages_str[1]
            if "`total_pages'" == "" local total_pages = 1
            capture destring pages_str, replace
        }

        * ---------------------------------------------------------------
        * Parse country-level records from the JSON
        * Strategy: split JSON on "},{"  to isolate each record, then
        * extract fields using regular expressions.
        * ---------------------------------------------------------------
        clear
        gen strL raw_json = ""
        set obs 1
        replace raw_json = fileread(`jsonfile')

        * Extract just the data array (second element of the outer array)
        * Find the start of the data array after the metadata object
        gen long data_start = strpos(raw_json, `"[{"')
        * Move past the metadata object - find the second [{
        gen strL remainder = substr(raw_json, data_start + 1, .)
        gen long second_bracket = strpos(remainder, `"[{"')

        * If there's no data array, skip
        if second_bracket[1] == 0 | data_start[1] == 0 {
            display as text "  -> No data on page `page'"
            local page = `page' + 1
            continue
        }

        gen strL data_json = substr(remainder, second_bracket, .)

        * Split records by splitting on the pattern  },{
        local data_str = data_json[1]
        clear

        * Count approximate number of records
        local remaining `"`data_str'"'
        local n_recs 0

        * Use a simpler approach: save data_json to file and parse line by line
        * Actually, let's use Stata's split approach with filewrite/fileread

        * Write each JSON object on its own line
        tempfile split_file
        tempfile records_dta

        clear
        set obs 1
        gen strL data = `"`data_str'"'

        * Replace },{ with a newline delimiter
        replace data = subinstr(data, `"},{"', `"}"' + char(10) + `"{"', .)

        * Remove outer brackets
        replace data = substr(data, 2, length(data) - 2) if substr(data, 1, 1) == "["
        replace data = substr(data, 1, length(data) - 1) if substr(data, length(data), 1) == "]"

        * Save to file and re-import line by line
        local data_content = data[1]

        clear
        tempfile lines_file
        file open fh using `lines_file', write replace
        file write fh `"`data_content'"'
        file close fh

        import delimited using `lines_file', delimiters("\n") varnames(nonames) clear stringcols(_all)

        rename v1 json_record
        local n_recs = _N

        * Parse fields from each JSON record
        gen str3   country_code = ""
        gen str100 country_name = ""
        gen double value_num    = .

        forvalues r = 1/`n_recs' {
            local rec = json_record[`r']

            * Extract countryiso3code
            if regexm(`"`rec'"', `""countryiso3code":"([^"]*)"') {
                quietly replace country_code = regexs(1) in `r'
            }

            * Extract country name (inside "country":{"id":"...","value":"..."})
            if regexm(`"`rec'"', `""country":\{"id":"[^"]*","value":"([^"]*)""') {
                quietly replace country_name = regexs(1) in `r'
            }

            * Extract value (could be a number or null)
            if regexm(`"`rec'"', `""value":([0-9.e+-]+)"') {
                local val = regexs(1)
                quietly replace value_num = real("`val'") in `r'
            }
        }

        * Keep parsed fields and add indicator metadata
        keep country_code country_name value_num
        rename value_num value

        gen str30 indicator  = "`ind'"
        gen str10 age_group  = "`alabel'"
        gen str10 gender     = "`glabel'"
        gen int   year       = `year'

        * Reorder to match master
        order country_code country_name indicator age_group gender year value

        local rec_count = `rec_count' + _N

        * Append to master
        append using `master'
        save `master', replace

        local page = `page' + 1

        * Small delay to be polite to the API
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

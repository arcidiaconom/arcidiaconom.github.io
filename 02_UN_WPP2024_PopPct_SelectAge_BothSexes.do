/*==============================================================================
  02_UN_WPP2024_PopPct_SelectAge_BothSexes.do
  Called from: run_all.do
  Expects globals:
      ${data_raw}

  What it does:
    - Creates: ${data_raw}/un_wpp2024/population
    - Downloads "Population Percentage by Select Age Groups – Both Sexes"
      XLSX from UN World Population Prospects 2024 (Standard Projections)
    - Saves the XLSX into that folder
    - Prints saved file path

  NOTE on URL: The UN WPP downloads page renders dynamically, so the direct
  link cannot be resolved automatically. The URL below was constructed from
  the confirmed WPP 2024 file-naming convention:

      https://population.un.org/wpp/downloads
        ?folder=Standard%20Projections&group=Population

  If the download fails, open that page in a browser, right-click the entry
  "Population Percentage by Select Age Groups – Both Sexes (XLSX)", copy the
  link address, and update the `url` local below.

==============================================================================*/

version 15.1
set more off



*------------------------------ Paths -----------------------------------------*
local base    "${data_raw}/un_wpp2024"
local outdir  "`base'/population"

* Output filename matches the UN's own naming convention; adjust if the
* actual filename on the downloads page differs.
local outfile "`outdir'/WPP2024_POP_F06_1_PERCENTAGE_POPULATION_SPECIFIC_AGE_GROUPS_BOTH_SEXES.xlsx"

* UN WPP 2024 — Population Percentage by Select Age Groups – Both Sexes
* TODO: verify URL from the downloads page (see header note above)
local url "https://population.un.org/wpp/Download/Files/1_Indicator%20(Standard)/EXCEL_FILES/2_Population/WPP2024_POP_F06_1_PERCENTAGE_POPULATION_SPECIFIC_AGE_GROUPS_BOTH_SEXES.xlsx"

*------------------------------ Create folders --------------------------------*
capture confirm dir "`base'"
if _rc mkdir "`base'"

capture confirm dir "`outdir'"
if _rc mkdir "`outdir'"

* Remove stale copy if present
capture erase "`outfile'"

*------------------------------ Download (robust) -----------------------------*
local ok = 0

* A) Try Stata copy with retries
forvalues a = 1/5 {
    if `ok'==1 continue, break
    capture noisily copy "`url'" "`outfile'", replace
    if !_rc {
        local ok = 1
        continue, break
    }
    di as txt "copy failed (rc=" _rc ") attempt `a'/5; retrying..."
    sleep 1500
}

* B) Fallback to curl / PowerShell if copy fails
if `ok'==0 {
    di as txt "Falling back to shell download..."
    if strpos(lower("`c(os)'"), "windows") {

        * Try curl (Windows 10+ often has it)
        capture noisily shell curl -L -o "`outfile'" "`url'"
        if !_rc & (fileexists("`outfile'")) local ok = 1

        * Try PowerShell if curl not available/blocked
        if `ok'==0 {
            capture noisily shell powershell -NoProfile -ExecutionPolicy Bypass ///
                -Command "try { Invoke-WebRequest -Uri '`url'' -OutFile '`outfile'' -UseBasicParsing } catch { exit 1 }"
            if !_rc & (fileexists("`outfile'")) local ok = 1
        }
    }
    else {
        * macOS/Linux
        capture noisily shell curl -L -o "`outfile'" "`url'"
        if !_rc & (fileexists("`outfile'")) local ok = 1
    }
}

if `ok'==0 {
    di as err "FAILED: Could not download UN WPP Population Percentage XLSX."
    di as err "Check proxy/network access to population.un.org and try again."
    di as err "If the URL has changed, update the `url' local at the top of"
    di as err "this script (see header note for instructions)."
    exit 601
}

di as res "Downloaded: `outfile'"
di as res "Done. Output folder: `outdir'"

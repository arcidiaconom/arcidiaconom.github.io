* Download World Bank Population Estimates and Projections
* Indicators: SP.POP.0004.FE, SP.POP.0004.MA, SP.POP.0509.FE
* Country: World | Years: 1990, 2050

* ssc install wbopendata

local indicators SP.POP.0004.FE SP.POP.0004.MA SP.POP.0509.FE

local i = 1
foreach ind of local indicators {
    wbopendata, indicator(`ind') country(WLD) year(1990:2050) long clear
    keep if year == 1990 | year == 2050
    tempfile f`i'
    save `f`i''
    local ++i
}

use `f1', clear
append using `f2' `f3'

export delimited using "population_data.csv", replace

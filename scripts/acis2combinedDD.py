from pathlib import Path
import json
import pandas as pd 
import numpy as np
import datetime as dt
import riverice_util as ru

prefix = "DD25"       # set to TDD for Thawing Degree Days
lastyear = 2024

config = {
    "TDD": {
        "deltaT": 32
    },
    "DD20": {
        "deltaT": 20
    },
    "DD25": {
        "deltaT": 25
    },
}

PROJPATH = Path().resolve().parent
datapath = PROJPATH / "data/weatherstations/ACIS/stationdata/RFC_new_model"
outpath = PROJPATH / f"data/weatherstations/ACIS/{prefix}"
climdir = outpath / "dd_climatologies"
stations = sorted(list(datapath.glob("*.csv")))
finalstations = PROJPATH / "data/stationdata_for_breakup/selectedstations.json"
datasuffix = "_T_max_min_avg_sd_swe.csv"

if __name__ == '__main__':
    with open(finalstations) as src:
        st = json.load(src)
    finalset = sorted(list(set(sum(st.values(), []))))

    clims = sorted(list(climdir.glob("*.csv")))
    nmissing = 10
    for fp in clims:
        name = fp.stem[:-14]
        if not name.replace('AIRPORT', 'AP') in finalset: 
            print(f"Excluding {name} - not in forecast")
            continue
        else: 
            print(f"Working on {name}")
        stationpth = datapath / f"{name}{datasuffix}"
        climdf = pd.read_csv(fp, header=4, index_col=0)
        testdf = ru.get_MAMJ_dd(ru.station2df(stationpth))
        missing = pd.DataFrame(testdf[testdf.Tavg_F==-9999].groupby('year').size().rename('count_missing'))
        significant_missing = missing[missing.count_missing > nmissing]
        missing_years = sorted(list(significant_missing.index))
        if 2024 in missing_years: missing_years.remove(2024)
        print(missing_years)
        print(name, missing_years)
        testdf = testdf[~testdf.year.isin(missing_years)]
        testdf['d_since_march1'] = list(testdf.index.to_series().apply(ru.days_past_march1))
        testdf['Tavg_clim'] = testdf.d_since_march1.apply(lambda x: climdf.iloc[x]['Tavg_F'])
        testdf = testdf.replace(-9999, np.nan)
        testdf['Tavg_F'] = testdf.Tavg_F.astype(float)
        testdf['Tavg_F'].fillna(testdf.Tavg_clim, inplace=True)
        testdf = testdf[['Tavg_F', 'year']]
        # make string for metadata for missing years
        if missing_years:
            missingstr = f"# Excluded years (more than {str(nmissing)} days of missing data): {', '.join(map(str, missing_years))}\n"
        else:
            missingstr = f"# No years excluded (all years had {str(nmissing)} or fewer days of missing data)\n"
        # write TDD files
        outdf = ru.get_pivotdf(ru.get_dddf(testdf), value='dd')
        with open(outpath / f"dd_bystation/{name}_yearly_DD.csv", 'w') as dst:
            dst.write(f"# {name}\n")
            dst.write(f"# Degree days egree days > {config[prefix]['deltaT']} starting March 1 from ACIS, gaps filled from climatology\n")
            dst.write(missingstr)
            dst.write("#\n")
            outdf.to_csv(dst, float_format='%.2f')
        # write cumul tdd files
        outdf = ru.get_pivotdf(ru.get_dddf(testdf))
        with open(outpath / f"dd_cumul_bystation/{name}_yearly_{prefix}_cumul.csv", 'w') as dst:
            dst.write(f"# {name}\n")
            dst.write(f"# Cumulative degree days > {config[prefix]['deltaT']} starting March 1 from ACIS, gaps filled from climatology\n")
            dst.write(missingstr)
            dst.write("#\n")
            outdf.to_csv(dst, float_format='%.2f')
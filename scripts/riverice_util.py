# Utility functions for river ice breakup project

import datetime as dt
import numpy as np
import pandas as pd
import seaborn as sb
from pathlib import Path
from matplotlib import pyplot as plt
from scipy.stats import pearsonr

DD_CONFIG = {
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
BREAKUPPTH = PROJPATH / "data/breakupdata/derived/breakupDate_cleaned.csv"
CLIMPTH = PROJPATH / "data/weatherstations/ACIS/TDD/all_cumul_clim1991_2020.csv"
STATIONDATA = PROJPATH / "data/weatherstations/ACIS/TDD/tdd_cumul_bystation"

def get_climpath(ddprefix):
    return PROJPATH / f"data/weatherstations/ACIS/{ddprefix}/all_cumul_clim1991_2020.csv"

def get_stationdata(ddprefix):
    return PROJPATH / f"data/weatherstations/ACIS/{ddprefix}/dd_cumul_bystation"

def datestr2dayssince(datestr: str, since: str = '0301') -> int:
    """Translate date string like '2000-04-02' into integer days-since reference date"""
    thedate = dt.datetime.strptime(datestr, '%Y-%m-%d').date()
    since_mth = int(since[:2])
    since_day = int(since[3:])
    since_date = dt.date(thedate.year, since_mth, since_day)
    return (thedate - since_date).days

def dayssince2date(days: int, year: int = '2000', since: str = '0301') -> dt.date:
    """Translate number of days past reference to dt.date for given year"""
    since_date = dt.datetime.strptime(f"{year}{since}", "%Y%m%d").date()
    return (since_date + dt.timedelta(days=days))

def retrieve_dd(row, stationDF, offset=0):
    try:
        return stationDF.iloc[row.days_since_march-offset][str(row.year)]
    except KeyError:
        return np.nan

def retrieve_dd_anomaly(row, stationname, stationDF, offset=0):
    climatologies = pd.read_csv(CLIMPTH, header=3, index_col=0)
    try:
        return ( stationDF.iloc[row.days_since_march1-offset][str(row.year)] 
                - climatologies[stationname].iloc[row.days_since_march1-offset] )
    except KeyError:
        return np.nan
    
def retrieve_dd_anomaly_fixed(row, stationname, stationDF, datestring):
    """Datestring is something like 04-15"""
    climatologies = pd.read_csv(CLIMPTH, header=3, index_col=0)
    days_since_march1 = datestr2dayssince(f"{str(row.year)}-{datestring}")
    try:
        return stationDF.iloc[days_since_march1][str(row.year)] - climatologies[stationname].iloc[days_since_march1]
    except KeyError:
        return np.nan

def calculate_corr(breakupDF: pd.DataFrame, 
                   locations: list[str], 
                   show_plots: bool = False, save_plots: bool = False, 
                   prefix: str = "DD_breakup", 
                   stationnames: list[str] | None = None,
                   outpath: Path = Path().resolve()) -> list[dict]:
    """Calculate pairwise correlations between DD anomalies in dataframe and stations, optionally plotting them"""
    if not set(locations) <= set(breakupDF.siteID):
        raise Exception("Sorry, the location isn't available in the breakup dataset. Check spelling?")
    outputrecords = []
    for location in locations:
        testDF = breakupDF[breakupDF.siteID == location].sort_values(
            by='year').reset_index(drop=True)
        if stationnames is None:
            stationnames = testDF.columns[5:]
        if not set(stationnames) <= set(breakupDF.columns):
            raise Exception("Sorry, the station isn't a valid name")
        for stationname in stationnames:
            result = testDF[stationname].corr(testDF['days_since_march1'],
                        method=lambda x, y: pearsonr(x, y))
            outputrecords.append(
                {
                    "stationname": stationname,
                    "location": location,
                    "pvalue": result.pvalue,
                    "rvalue": result.statistic,
                    "r2value": result.statistic**2
                }
            )
            if show_plots or save_plots:
                sb.regplot(data=testDF, y='days_since_march1', x=stationname, scatter=False)
                ax = sb.scatterplot(data=testDF, y='days_since_march1', x=stationname, 
                                    hue='year', palette="crest")
                ax.set_title(f"{stationname.replace('_', ' ').title()} station for {location} "
                             f"{prefix.replace('_', ' ')}")
                ax.set_xlabel(f"DD anomaly")
                ax.set_ylabel("Days since March 1")
                plt.legend(loc='upper right')
                ax.text(0.06, 0.1, 
                        f'r = {result.statistic:.2f}\nr2 = {result.statistic**2:.2f}\np = {result.pvalue:.2E}', 
                        transform=ax.transAxes)
                if show_plots:
                    plt.show()
                if save_plots:
                    fn = f"{prefix}_{location.replace(' ', '_')}_AT_{stationname}.png"
                    plt.savefig(outpath / fn, bbox_inches='tight')
                    plt.close()
    return outputrecords
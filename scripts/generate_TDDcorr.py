import riverice_util as rutil
from pathlib import Path
import datetime as dt
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)
PREFIX = "DD25"
BREAKUPPTH = rutil.BREAKUPPTH
CLIMPTH = rutil.get_climpath(PREFIX)
STATIONDATA = rutil.get_stationdata(PREFIX)
OUTPATH = rutil.PROJPATH / "data/breakupdata/working"

## Change these as needed 
STARTDATE = dt.datetime(2000, 4, 1)
NUMDAYS = 90

def makeDF_from_records(records: list[dict[str]]) -> pd.DataFrame:
    """"Turn per-station, per-location, per-date records of correlations into dataframe"""
    outdf = pd.DataFrame.from_records([
        {'date': item, 'stationname': subitem['stationname'], 
        'location': subitem['location'], 'r2': subitem['r2value'],
        'r': subitem['rvalue'], 'p': subitem['pvalue']} 
            for item in records for subitem in records[item]])
    outdf.fillna(0, inplace=True)
    outdf['dummydate'] = '2000-'+ outdf['date']
    outdf['DateStamp'] = pd.to_datetime(outdf['dummydate'], format='%Y-%m-%d')
    outdf['stationname'] = outdf['stationname'].str.replace('AIRPORT', 'AP')
    outdf['stationname'] = outdf['stationname'].str.replace('INTERNATIONAL', 'INTL')
    outdf.drop(columns=['dummydate'], inplace=True)
    return outdf

def get_correlationrecords(station_dd: list[Path], 
                           breakupDF: pd.DataFrame,
                           datestr: str,
                           locations: list[str]) -> list:
        for pth in station_dd:
            stationname = pth.stem[:(-14-len(PREFIX))]
            logging.debug(f"   working on {stationname}")
            teststationDF = pd.read_csv(pth, skiprows=4, index_col=0)
            breakupDF[stationname] = breakupDF.apply(
                lambda row: rutil.retrieve_dd_anomaly_fixed(row, stationname, teststationDF, datestr), axis=1)
        returnrec = rutil.calculate_corr(breakupDF, locations)
        return returnrec

if __name__ == '__main__':
    breakup = pd.read_csv(BREAKUPPTH, header=3, index_col=0)
    breakup['days_since_march1'] = breakup.apply(lambda row: rutil.datestr2dayssince(row.breakup), axis=1)
    logging.info(f"Read breakup DataFrame, {len(breakup)} lines")
    climatologies = pd.read_csv(CLIMPTH, header=3, index_col=0)
    station_dd = sorted(list(STATIONDATA.glob("*.csv")))
    locations = breakup.siteID.unique()
    logging.info("Successfully read climatologies, stations, and locations.")

    # Retrieve records for each correlation  dataframe 
    records = {}
    try:
        for ii in range(NUMDAYS):
            datepoint = STARTDATE + dt.timedelta(days=ii)
            datestr = datepoint.strftime('%m-%d')
            print(f"Working on {datestr}")
            breakup_anomaly_fixed = breakup.copy()
            records[datestr] = get_correlationrecords(
                station_dd, breakup_anomaly_fixed, datestr, locations) 
    finally:
        recordsDF = makeDF_from_records(records)

    with open(OUTPATH / f"{PREFIX}_anomaly_correlations.csv", "w") as dst:
        dst.write(f"# Correlations between {PREFIX} anomalies each date since April 1 and breakup day \n")
        dst.write("# For all selected sites and stations\n")
        dst.write("# \n")
        recordsDF.to_csv(dst)

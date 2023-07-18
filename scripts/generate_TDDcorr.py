import riverice_util as rutil
from pathlib import Path
import datetime as dt
import pandas as pd

BREAKUPPTH = rutil.BREAKUPPTH
CLIMPTH = rutil.CLIMPTH
STATIONDATA = rutil.STATIONDATA
OUTPATH = rutil.PROJPATH / "data/breakupdata/working"

## Change these as needed 
STARTDATE = dt.datetime(2000, 4, 1)
NUMDAYS = 65

def makeDF_from_records(records: list[dict[str]]):
    """"Turn per-station, per-location, per-date records of correlations into dataframe"""
    outdf = pd.DataFrame.from_records([
    {'date': item, 'stationname': subitem['stationname'], 
     'location': subitem['location'], 'r2': subitem['r2value'],
     'r': subitem['rvalue'], 'p': subitem['pvalue']} 
    for item in records for subitem in records[item]])
    outdf.fillna(0, inplace=True)
    outdf['dummydate'] = '2000-'+ outdf['date']
    outdf.drop(columns=['dummydate'], inplace=True)
    outdf['DateStamp'] = pd.to_datetime(outdf['dummydate'], format='%Y-%m-%d')
    outdf['stationname'] = outdf['stationname'].str.replace('AIRPORT', 'AP')
    outdf['stationname'] = outdf['stationname'].str.replace('INTERNATIONAL', 'INTL')
    return outdf

def get_correlationrecords(station_tdd: list[Path], 
                           datepoint: dt.datetime,
                           locations: list[str]):
        for pth in station_tdd:
            stationname = pth.stem[:-17]
            teststationDF = pd.read_csv(pth, skiprows=4, index_col=0)
            breakup_anomaly_fixed[stationname] = breakup_anomaly_fixed.apply(
                lambda row: rutil.retrieve_tdd_anomaly_fixed(row, stationname, teststationDF, datestr), axis=1)
        returnrec = rutil.calculate_corr(breakup_anomaly_fixed, locations)
        records[datestr] = returnrec
        return records

if __name__ == '__main__':

    breakup = pd.read_csv(BREAKUPPTH, header=3, index_col=0)
    climatologies = pd.read_csv(CLIMPTH, header=3, index_col=0)
    station_tdd = sorted(list(STATIONDATA.glob("*.csv")))
    locations = breakup.siteID.unique()

    # Retrieve records for each correlation  dataframe 
    records = {}
    for ii in range(NUMDAYS):
        datepoint = STARTDATE + dt.timedelta(days=ii)
        datestr = datepoint.strftime('%m-%d')
        breakup_anomaly_fixed = breakup.copy()






#!/usr/bin/env python
# 
# 2023-02-28 cwaigl@alaska.edu

import csv
from pathlib import Path
import requests
import pandas as pd
import geopandas as gp
import numpy as np

PROJPATH = Path(__file__).resolve().parent.parent
OUTDIR = PROJPATH / "data/weatherstations/NBM"
ACISDIR = PROJPATH / "data/weatherstations/ACIS"
REGENERATE_SUMMARY = False
REGENERATE_ACISSTATIONS = True
OVERWRITE = False
SUMMARYFILE = "ACIS_newmodel_forNBM.csv"
ACISSTATIONS = "ACIS_stations_AK_fornewmodel.csv"

def safelyget(alist, idx, default='N/A'):
    """Returns alist[idx] if exists, else default"""
    try:
        return alist[idx]
    except (KeyError, IndexError):
        return default

def write_rfc_stations(filelist):
    stationcodes = []
    for fpth in filelist:
        print()
        with open(fpth) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                stationcodes.append([fpth.stem[:-4]] + row)
    stationdf = pd.DataFrame.from_records(stationcodes)
    stationdf.columns = [
        'breakuploc', 'ICAO', 'weight', 'GSODURL', 'ID', 'lat', 'lon'
    ]
    outfp = OUTDIR / SUMMARYFILE
    outfp.parent.mkdir(parents=True, exist_ok=True)
    stationdf.to_csv(outfp, index=False)
    return stationdf

def get_stationcodes(filelist):
    stationcodes = []
    for fpth in filelist:
        with open(fpth) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                stationcodes.append(row[0])
    return sorted(list(set(stationcodes)))
    
def get_acis_stationmeta(stationlist):
    sidsvalue = ','.join(stationlist)
    print(sidsvalue)
    baseurl = 'http://data.rcc-acis.org/StnMeta'
    params = {
        'sids': sidsvalue,
        'meta': "name,uid,sids,ll,elev,valid_daterange",
    }
    resp = requests.get(url=baseurl, params=params)
    return resp.json()['meta']

def sidslist_to_dict(sidslist):
    return {
        item.split(' ')[1]: item.split(' ')[0]
        for item in sidslist
    }

def postprocess_acis(stationdat):
    """stationdat is JSON returned by ACIS"""
    records = [   
        dict(
            name=stat['name'],
            acisID=stat['uid'],
            ICAO=safelyget(sidslist_to_dict(stat['sids']), '5', ''),
            NWSID=safelyget(sidslist_to_dict(stat['sids']), '7', ''),
            longitude=safelyget(safelyget(stat, 'll', []), 0, np.nan),
            latitude=safelyget(safelyget(stat, 'll', []), 1, np.nan),
            elev_ft=safelyget(stat, 'elev', np.nan), 
            # valid_avgT_start=safelyget(stat['valid_daterange'][0], 0, ''),
            # valid_avgT_end=safelyget(stat['valid_daterange'][0], 1, ''),
            # valid_snowdepth_start=safelyget(stat['valid_daterange'][1], 0, ''),
            # valid_snowdepth_end=safelyget(stat['valid_daterange'][1], 1, ''),
        )
        for stat in stationdat
    ]
    stationDF = pd.DataFrame.from_records(records)
    return stationDF


if __name__=='__main__':
    

    stations = pd.read_csv(ACISDIR / ACISSTATIONS)
    
    idcodes = sorted(map(str, list(set(stations['acisID']))))
    print(f"RFC model stations loaded. There are {len(idcodes)} unique station codes.\n")
    print("Getting station info from ACIS")

    stationdat = get_acis_stationmeta(idcodes)
    print(f"There are {len(stationdat)} stations in ACIS")
    stationDF = postprocess_acis(stationdat)
    # stationDF.to_csv(OUTDIR / SUMMARYFILE, index=False)
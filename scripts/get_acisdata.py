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
ACISDIR = PROJPATH / "data/weatherstations/ACIS"
OUTDIR = ACISDIR / 'stationdata/RFC_new_model'
ACISSTATIONS = "ACIS_stations_AK_fornewmodel.csv"
RUNYEAR = 2025

def safelyget(alist, idx, default='N/A'):
    """Returns alist[idx] if exists, else default"""
    try:
        return alist[idx]
    except (KeyError, IndexError):
        return default

def get_acis_stationdata(uid):

    baseurl = 'http://data.rcc-acis.org/StnData'
    params = {
        'uid': uid,
        'sdate': "1980-01-01",
        'edate': f"{RUNYEAR}-06-30",
        'elems': "maxt,mint,avgt,snwd,13",
        'output': 'csv'
    }
    resp = requests.get(url=baseurl, params=params)
    return resp.text

if __name__=='__main__':
    # get station file
    stations = pd.read_csv(ACISDIR / ACISSTATIONS)

    for idx, record in stations.iterrows():
        outfn = f"{record['name'].replace(' ', '_')}_T_max_min_avg_sd_swe.csv"
        print(f"getting {outfn}")
        out = get_acis_stationdata(record['acisID'])
        with open(OUTDIR / outfn, 'w') as dst:
            dst.write(out)


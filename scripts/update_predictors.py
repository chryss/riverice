#!/usr/bin/env python
# 
# 2023-02-28 cwaigl@alaska.edu

from pathlib import Path
import urllib.request
import pandas as pd
import geopandas as gp
import numpy as np
import argparse
from fiweps.data import d_urls

OUTPATH = Path("/Users/christine/Projects/2023_Riverice/data/working/predictors")
RAWPREDPATH = OUTPATH
STARTYEAR = 1980

def parse_arguments():
    parser = argparse.ArgumentParser(description='Download new predictor data and update dataframe')
    parser.add_argument('-d', '--download',
        help='download new files',
        action='store_true')
    parser.add_argument('-d', '--dataframe',
        help='make new dataframe',
        action='store_true')
    parser.add_argument('-a', '--all',
        help='all steps',
        action='store_true')
    return parser.parse_args()

def get_data(row):
    columns = ['Year'] + [str(ii) for ii in range(1, 13)]
    fp = RAWPREDPATH / f"{row['name']}.txt"
    data = pd.read_csv(fp, skiprows=1, skipfooter=row.skipfooter, delim_whitespace=True, names=columns,
                       engine='python')
    data = data.astype(float)
    data['Year'] = data['Year'].astype(int)
    data.replace(row.nodata, np.nan, inplace=True)
    data = data[data['Year'] >= STARTYEAR]
    data.meta = row['shortname']
    return data

if __name__ == '__main__':
    
    args = parse_arguments()
    if args.download or args.all:
        for record in d_urls.TELECONNECTIONURLS:
            print(f"retrieving {record['name']} from {record['URL']}")
            urllib.request.urlretrieve(record['URL'], OUTPATH / f"{record['name']}.txt")
            # print(d_urls.TELECONNECTIONURLS)

    if args.dataframe or args.all:
        



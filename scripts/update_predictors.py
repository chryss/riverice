#!/usr/bin/env python
# 
# 2023-02-28 cwaigl@alaska.edu

from pathlib import Path
import urllib.request
import pandas as pd
import geopandas as gp
import numpy as np
from fiweps.data import d_urls

OUTPATH = Path("/Users/christine/Projects/2023_Riverice/data/working/predictors")

if __name__ == '__main__':
    
    for record in d_urls.TELECONNECTIONURLS:
        print(f"retrieving {record['name']} from {record['URL']}")
        urllib.request.urlretrieve(record['URL'], OUTPATH / f"{record['name']}.txt")
        # print(d_urls.TELECONNECTIONURLS)


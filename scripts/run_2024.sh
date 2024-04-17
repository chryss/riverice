#!/bin/bash

ACISDIR="../data/weatherstations/ACIS/stationdata/RFC_new_model"
OUTDIR="../data/DDforecast_2024"
CLOUDDIR="/Users/chris/Library/CloudStorage/GoogleDrive-cwaigl@alaska.edu/My\ Drive/Shortcuts/Alaska\ River\ Ice\ Forecasting/Forecasts2024/from_DD25_only"

SCRIPTDIR=`pwd`

conda activate fiweps

# refresh ACIS data for model stations
python get_acisdata.py
# rename Nenana station 
mv ${ACISDIR}/NENANA_MUNICIPAL_AIRPORT_T_max_min_avg_sd_swe.csv ${ACISDIR}/NENANA_MUN_AP_T_max_min_avg_sd_swe.csv
# generate combined DD25 datasets for each location
python acis2combinedDD.py
# run new forecast
python make_forecast_2024.py 

echo "Copying to Google Drive"
cd $OUTDIR
cp -R  * ${CLOUDDIR}
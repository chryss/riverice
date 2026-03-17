#!/bin/bash


ACISDIR="../data/weatherstations/ACIS/stationdata/RFC_new_model"
OUTDIR="../data/DDforecast_2026"
CLOUDDIR='/Users/chris/Library/CloudStorage/GoogleDrive-cwaigl@alaska.edu/.shortcut-targets-by-id/16EqbrP-7DV4rvd2MNBbqmaRmYh5OtqsW/Alaska River Ice Forecasting/Forecasts2026'
SCRIPTDIR=`pwd`

# run in activated conda environment
# conda init
# conda activate aprfc_breakup

# refresh ACIS data for model stations
python get_acisdata.py
# rename Nenana station 
# mv ${ACISDIR}/NENANA_MUNICIPAL_AIRPORT_T_max_min_avg_sd_swe.csv ${ACISDIR}/NENANA_MUN_AP_T_max_min_avg_sd_swe.csv
# generate combined DD25 datasets for each location
python acis2combinedDD.py
# run new forecast
python make_forecast.py 

echo "Copying to Google Drive"
cd ${OUTDIR}
cp -R  * ${CLOUDDIR}

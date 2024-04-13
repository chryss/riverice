#!/bin/bash

ACISDIR="../data/weatherstations/ACIS/stationdata/RFC_new_model"
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

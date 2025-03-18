## Instructions for the use of the Jupyter Notebooks and Python scripts

Author: Chris Waigl, IARC/UAF, cwaigl@alaska.edu

### General & environment considerations 

* You have several choices to install this code in order to run the model. a) Use `git clone` to obtain your own version of the repository. You can periodically use `git pull` to integrate changes. b) (more advanced) Create a fork of the repository in the GitHub user interface. In this case you can send me suggestions for changes via pull requests. c) (more basic) Download the latest release from the GitHub user interface. In this case you just get a zip file with code, no integration with version control. You'll update the code by re-downloading a newer version. 
* The file `requirements.txt` contains the Python libraries and current versions used during development. Newer versions should be fine, but if a library makes backwards-incompatible changes, these versions are "safe".
* If conda is to be used to manage the Python environment the file `requirements.yml` can be used to create a conda environment with the command `conda env create -f requirements.yml` 
* If conda is used, the module `nb-clean` will be installed, and it is generally desirable.  It makes it a lot easier to deal with Git and Jupyter Notebooks. This only applies if you clone the repository from GitHub. After all modules are installed in the environment (with conda or otherwise) please run `nb-clean add-filter --preserve-cell-outputs --remove-empty-cells` while in the repository root. However, if you download a release, you are not creating your own git repository and `nb-clean` will not be able to add a filter. 

### Preparation code - to be run to set up a new modelling effort. 

*When prototyping, write outputs to `breakupdata/working` directory and then move manually to final location*

1. `ACIS_API_explore` to retrieve a clean copy of valid ACIS stations 
2. `APRFC_breakupdata_clean.ipynb` to reload and clean up APRFC breakup table and calculate average breakup date from newest data
3. Edit `get_acisdata.py` and update year to current 
4. It is unlikely that the DD25 climatologies need to be updated. They've been calculated for the 1991-2020 period . If necessary, use `ACIS_temp2dd.ipynb` followed by `ACIS_ddcumulclimatology.ipynb`

### To integrate new locations:

3. Core data files are already in the repository under `data/` 
4. `APRFC_breakupdata_correlate.ipynb`
4. The heavy lifting is done by the script `generate_DDcorr.py`
5. `APRFC_breakupdata_stationselect.ipynb`  to generate `selectedstations.json` 
6. `APRFC_ACIS_combinedstations.ipynb` - this is prototyping for the `acis2combinedDD.py` script which runs daily (see below)

### Daily runs

1. Core data files are already in the repository under `data/` 
1. `get_acisdata.py` to update the ACIS data
2. `acis2combinedDD.py` to update the daily and cumulative DD tables and combine station data into averaged DD values as per `selectedstations.json`
3. `make_forecast_2024.py` runs the statistics and generates plots and reports

These three scripts can be automated via `run_2025.sh` which is a shell script. It needs to be edited before first run (name of enironment and how to load it, path of shared drive....)




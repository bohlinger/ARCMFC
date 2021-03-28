# ARCMFC
Scripts for ARCMFC related tasks

### Main developer and moderation:
Patrik Bohlinger, Norwegian Meteorological Institute, patrikb@met.no

## Purpose
This package contains scripts that define the workflow for ARCMFC related tasks. 
Those tasks comprise:
* Downloading Sentinel-3A (s3a) level-3 satellite altimetry data
* Retrieve in-situ data and write to netCDF4 file
* Collocation of in-situ observations with the ARCMFC wave model and write to nc
* Collocation of s3a footprints with the ARCMFC wave model and write to nc
* Read from in-situ files and write to monthly netCDF4 ARCMFC report files
* Read from satellite files and create validation statistics files
* make validation figures and update webpage

## Used data
The satellite data is obtained from http://marine.copernicus.eu/services-portfolio/access-to-products/?option=com_csw&view=details&product_id=WAVE_GLO_WAV_L3_SWH_NRT_OBSERVATIONS_014_001. In-situ data is obtained at offshore platforms and retrieved from internally stored .d22-files. ARCMFC Model data is retrieved from the publicly accessable MET Norway's thredds server but can also be obtained via Copernicus.

## Used software
The scripts build on the "wavy" software which is openly available at github.

## Additional info
The collocation method follows Bohlinger et al. (2019): https://www.sciencedirect.com/science/article/pii/S1463500319300435.

## Getting started
### Installing wavy
1. First download or clone the wavy github repository:
```
git clone --single-branch --branch ARCMFC git@github.com:bohlinger/wavy.git
```
Info on how-to clone a repository:
https://help.github.com/en/articles/cloning-a-repository

2. To make it consistent with the description in this README please use as target location your home directory e.g.: ~/wavy.

3. Install wavy using conda using the environment.yml like:
```
cd ~/wavy
conda env create -f environment.yml
conda activate wavy
```
Info on installing conda, e.g.:
https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html

4. Append to PYTHOPATH like:
```
export PYTHONPATH=$PYTHONPATH:/home/${USER}/wavy/wavy
```
5. Configuration files are organized under wavy/config and might need adjustments according to your plans. Examples are the locations of your wave model output files or observation data (e.g. satellite altimetry data). What is needed for this workshop is shown below.

6. Prepare access to Copernicus products. Enter your account credentials into the .netrc-file. Your .netrc should look something like:
```
machine nrt.cmems-du.eu    login {USER}  password {PASSWORD}
```

7. Prepare your wavy environment with providing the directories for satellite data and model data. There are multiple config files but we only need to worry about a few for now. Explore the config file for satellites like this:
```
cd ~/wavy/config
vim satellite_specs.yaml
```
Add your path for satellite data here under cmems:
```
    cmems:
        level: 3
        satellite: s3a, s3b, c2, al, j3, h2b, cfo
        local:
            path: /path/to/satellite/files
```
The path could be defined e.g. like: path: /home/${USER}/tmp_altimeter
### HELP
Executable files usually have help function which can be read using e.g.:
```
./{YourExecutable}.py -h
```

e.g.:
```
cd ~/wavy/wavy
./download.py -h
```

## Workflow
### Download satellite data 
- [x] defined in: satellite_specs.yaml
```
./download.py -sat s3a -sd 2020103000 -ed 2020111000
```
As input the start date (sd) and the end date (ed) are required. If those are None, the last 24 hours are download. The data is automatically organized in {path}/{year}/{month}.

### Retrieve in-situ data
- [x] defined in station_specs.yaml, d22_var_dicts.yaml
```
./collect_stat.py -sd 20201030000 -ed 2020111000
```
or to cover only the previous day
```
./collect_stat.py
```
### Collocation of in-situ data with model
- [x] defined in model_specs.yaml, station_specs.yaml, d22_var_dicts.yaml, collocation_specs.yaml
```
./collocate_stat.py -platform ekofisk -sensor waverider -sd 2020103000 -ed 2020111000
```
... or for all stations/sensors:
```
./collocate_stat.py -sd 2020103000 -ed 2020111000
```
... or for the previous day simply:
```
./collocate_stat.py
```
### Collocation of satellite data with ARCMFC model
- [x] defined in satellite_specs.yaml, model_specs.yaml, collocation_specs.yaml
```
./collocate_sat.py -sat s3a -mod ARCMFC3 -sd 2020103000 -ed 2020111000
```
... or for the previous day simply:
```
./collocate_sat.py -sat s3a -mod ARCMRC3
```
### From in-situ files to monthly netCDF4 ARCMFC files
```
./make_monthly_ARCMFC_file.py -d 202011
```

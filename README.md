# ARCMFC
Scripts for ARCMFC related tasks

### Main developer and moderation:
Patrik Bohlinger, Norwegian Meteorological Institute, patrikb@met.no

## Purpose
This package contains scripts that define the workflow for ARCMFC related tasks. 
Those tasks comprise:
1. Downloading Sentinel-3A (s3a) level-3 satellite altimetry data
2. Collocation of s3a footprints and in-situ platform based observations with the ARCMFC 3km wave model.
3. Writing the collocated time series to netCDF4 files
4. Reading from files from 3. and writing to monthly netCDF4 ARCMFC report files
5. Reading from files from 3. and compute validation files
6. Based on files from 3. and 5. make validation figures and update webpage

## Used data
The satellite data is obtained from http://marine.copernicus.eu/services-portfolio/access-to-products/?option=com_csw&view=details&product_id=WAVE_GLO_WAV_L3_SWH_NRT_OBSERVATIONS_014_001. In-situ data is obtained at offshore platforms and retrieved from internally stored .d22-files. Model data is retrieved from MET Norway's thredds server.

## Used software
The scripts build on the "wavy" software which is openly available at github.

## Additional info
The collocation method follows Bohlinger et al. (2019): https://www.sciencedirect.com/science/article/pii/S1463500319300435.

## Getting started
### Installing wavy
1. First download or clone the wavy github repository:
```
git clone --single-branch --branch ARCMFC https://github.com/bohlinger/wavy.git
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

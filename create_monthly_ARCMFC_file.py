#!/usr/bin/env python

import netCDF4
from datetime import datetime,timedelta
import yaml
from dateutil.relativedelta import relativedelta
import numpy as np
import os
import calendar
from copy import deepcopy

from ncmod import get_arcmfc_stats
from validationmod import calc_rmsd

"""
Script to create monthly ARCMFC files
Consists of:
    - read all collocation files
    - compute stats
    - create netcdf file skeleton
    - write to netcdf file
"""
leadtimes = [12, 36, 60, 84, 108, 132, 156, 180, 204, 228]

# get variable info
configfile = os.path.abspath(os.path.join(os.path.dirname( __file__ ), \
                            'config/station_specs_ARCMFC.yaml'))
with open(configfile,'r') as stream:
    station_dict=yaml.safe_load(stream)


now = datetime.now()
#now = datetime(2021,2,5)
filedate = now - relativedelta(months=1) # converts to previous month

def validation(filedate,leadtime,station_dict):
    inpath = filedate.strftime('/home/patrikb/tmp_collocation/ARCMFC3/%Y/%m/')
    mop,mor,nov,msd = [],[],[],[]
    datelst = []
    sdate = datetime(filedate.year, filedate.month,1)
    edate = datetime(filedate.year, filedate.month,
            calendar.monthrange(filedate.year, filedate.month)[1],23)
    tmpdate = sdate
    print('sdate',sdate)
    print('edate',edate)
    while tmpdate <= edate:
        print('tmpdate',tmpdate)
        mods = []
        obs = []
        # get data
        for platform in station_dict['platform']:
            sensor = list(station_dict['platform'][platform]\
                                        ['sensor'].keys())[0]
            filestr = filedate.strftime(   "superobbed_Hs_ARCMFC3_vs_"
                                    + platform + "_"
                                    + sensor + "_coll_ts_lt"
                                    + "{:0>3d}".format(leadtime)
                                    + "h_%Y%m.nc" )
            nc = netCDF4.Dataset(inpath+filestr,mode='r')
            time = nc.variables['time']
            dt = list(netCDF4.num2date(time[:],time.units))
            time_unit = time.units
            if tmpdate in dt:
                mod = float(nc.variables['model_values'][dt.index(tmpdate)])
                ob = float(nc.variables['obs_values'][dt.index(tmpdate)])
            else:
                mod = np.nan
                ob = np.nan
            nc.close()
            mods.append(mod)
            obs.append(ob)
        # compute skill scores
        mods = np.array(mods)
        obs = np.array(obs)
        comb = mods + obs
        idx = np.array(range(len(comb)))[~np.isnan(comb)].astype('int')
        mop.append(np.mean(mods[idx]))
        mor.append(np.mean(obs[idx]))
        nov.append(len(idx))
        msd.append(calc_rmsd(mods,obs)[0])
        datelst.append(tmpdate)
        tmpdate += timedelta(hours=6)

    validation_dict = { 'mop':mop,
                        'mor':mor,
                        'nov':nov,
                        'msd':msd,
                        'datelst':datelst,
                        'time_unit':time_unit }
    return validation_dict

def create_monthly_nc(filedate,leadtimes,station_dict):
    # make outpath
    outpath = filedate.strftime('/home/patrikb/tmp_monthly_ARCMFC/%Y/%m/')
    os.system('mkdir -p ' + outpath)
    # produce netcdf file:
    nc = netCDF4.Dataset(os.path.join(outpath,\
        'product_quality_stats_ARCTIC_ANALYSIS_FORECAST_WAV_002_014_'
        + filedate.strftime('%Y')
        + filedate.strftime('%m')
        + '01-'
        + filedate.strftime('%Y') + filedate.strftime('%m')
        + str(calendar.monthrange(  filedate.year,
                                    filedate.month)[1]) + '.nc'),'w')
    nc.contact = 'patrikb@met.no'
    nc.product = 'Arctic wave model WAM'
    nc.production_centre = 'Arctic MFC'
    nc.production_unit = 'Norwegian Meteorological Institute'
    nc.creation_date = str(datetime.now())
    nc.thredds_web_site = ('http://thredds.met.no/thredds/myocean/'\
                            +'ARC-MFC/mywave-arctic.html')

    ncdims = {  'string_length':28, 'areas':3, 'metrics':4, \
                'surface':1, 'forecasts':10  } # and time, unlim
    metric_names = [name.ljust(28) for name in ["mean of product",
                                                "mean of reference",
                                                "mean square difference",
                                                "number of data values"]]
    area_names = [name.ljust(28) for name in ["North Sea and Norwegian Sea",
                                              "Full domain",
                                              "Nordic Seas"]]
    dimsize = None
    dimtime = nc.createDimension(
                                'time',
                                size=dimsize
                                )
    nc_time = nc.createVariable(
                               'time',
                               np.float64,
                               dimensions=('time')
                               )
    for name,dim in ncdims.items():
        nc.createDimension(name,size=dim)

    nc_time.long_name = 'validity time'

    nc_metricnames = nc.createVariable('metric_names','S1', \
                        dimensions=(u'metrics',u'string_length'))
    def split(word):
        return [char for char in word]
    for i in range(4):
        nc_metricnames[i,:] = split(metric_names[i])

    nc_areanames = nc.createVariable('area_names','S1', \
                    dimensions=(u'areas',u'string_length'))
    for i in range(3):
        nc_areanames[i,:] = split(area_names[i])
    nc_areanames.long_name = 'area names'
    nc_areanames.description = 'region over which statistics are aggregated'

    nc_leadtime = nc.createVariable('forecasts','f4',dimensions=('forecasts'))
    nc_leadtime.long_name = 'forecast lead time'
    nc_leadtime.units = 'hours'
    nc_leadtime[:] = np.arange(12,229,24)

    ncvar = nc.createVariable('stats_VHM0_platform','f4',
                dimensions=('time', 'forecasts', 'surface', \
                            'metrics', 'areas'), fill_value=1e35)#9999.)
    ncvar.standard_name = 'sea_surface_wave_significant_height'
    ncvar.parameter = 'stats_VHM0_platform'
    ncvar.units = 'm'
    ncvar.reference_source = 'wave data from offshore platforms '\
                            +'available from d22 files at the '\
                            +'Norwegian Meteorological Institute'


    print ("Add platform statistics")
    for l in range(len(leadtimes)):
        print('Validate for leadtime:',leadtimes[l])
        validation_dict = validation(filedate,leadtimes[l],station_dict)
        ncvar[:,l,0,0,0] = validation_dict['mop']
        ncvar[:,l,0,1,0] = validation_dict['mor']
        ncvar[:,l,0,2,0] = validation_dict['msd']
        ncvar[:,l,0,3,0] = validation_dict['nov']

    nc_time.units = "days since 2001-01-01 12:00:00 UTC"
    nc_time[:] = netCDF4.date2num(  validation_dict['datelst'],
                                    units="days since 2001-01-01 12:00:00 UTC")

    print ("Add altimeter statistics")
    end_date = netCDF4.num2date(nc_time[-1],units=nc_time.units)
    start_date = netCDF4.num2date(nc_time[0],units=nc_time.units)
    tmp_date = deepcopy(start_date)
    M=np.ones([len(nc_time),10,1,4,1])*1e35#9999.
    dictlst_all=[]
    excepts_all=[]
    count1 = 0
    # region: full domain
    while (tmp_date <= end_date):
        print (count1)
        dictlst = []
        excepts = []
        count2 = 0
        for lt in leadtimes:
            inpath=('/home/patrikb/tmp_validation/ARCMFC3/'
                    + tmp_date.strftime('%Y')
                    + '/'
                    + tmp_date.strftime('%m')
                    + '/')
            filename_stats = tmp_date.strftime(
                                "Hs_ARCMFC3_vs_s3a_for_ARCMFC3_val_ts_lt"
                                + "{:0>3d}".format(lt)
                                + "h_%Y%m.nc")
            print(inpath + filename_stats)
            try:
                valid_dict, dtime = get_arcmfc_stats(inpath + filename_stats)
                idx = list(dtime).index(tmp_date)
                dictlst.append(valid_dict)
                dictnames=['mop','mor','msd','nov']
                for i in range(len(dictnames)):
                    M[count1,count2,0,i,0]=valid_dict[dictnames[i]][idx]
            except ValueError:
                pass
            count2=count2+1
        count1=count1+1
        dictlst_all.append(dictlst)
        excepts_all.append(excepts)
        tmp_date = tmp_date + timedelta(hours=6)

    # append to netcdf
    nc_stats_VHM0_altimeter = nc.createVariable(
                        'stats_VHM0_altimeter',
                        np.float64,
                        dimensions=('time',
                        'forecasts',
                        'surface',
                        'metrics',
                        'areas',),
                        fill_value=1e35)#9999.)
    nc.variables["stats_VHM0_altimeter"][:,:,:,:,1] = M[:,:,:,:,0]
    nc_stats_VHM0_altimeter.standard_name = \
                            "sea_surface_wave_significant_height"
    nc_stats_VHM0_altimeter.parameter = "stats_VHM0_altimeter"
    nc_stats_VHM0_altimeter.units = "m"
    nc_stats_VHM0_altimeter.reference = \
                            "wave data from Sentinel-3a altimeter"
    nc_stats_VHM0_altimeter.reference_source = \
                            "WAVE_GLO_WAV_L3_SWH_NRT_OBSERVATIONS_014_001"

    # region: Nordic Seas
    end_date = netCDF4.num2date(nc_time[-1],units=nc_time.units)
    start_date = netCDF4.num2date(nc_time[0],units=nc_time.units)
    tmp_date = deepcopy(start_date)
    M=np.ones([len(nc_time),10,1,4,1])*1e35#9999.
    dictlst_all=[]
    excepts_all=[]
    count1 = 0
    while (tmp_date <= end_date):
        print (count1)
        dictlst = []
        excepts = []
        count2 = 0
        for lt in leadtimes:
            inpath=('/home/patrikb/tmp_validation/ARCMFC3/'
                    + tmp_date.strftime('%Y')
                    + '/'
                    + tmp_date.strftime('%m')
                    + '/')
            filename_stats = tmp_date.strftime(
                                "Hs_ARCMFC3_vs_s3a_for_NordicSeas_val_ts_lt"
                                + "{:0>3d}".format(lt)
                                + "h_%Y%m.nc")
            print(inpath + filename_stats)
            try:
                valid_dict, dtime = get_arcmfc_stats(inpath + filename_stats)
                print(valid_dict)
                idx = list(dtime).index(tmp_date)
                dictlst.append(valid_dict)
                dictnames=['mop','mor','msd','nov']
                for i in range(len(dictnames)):
                    M[count1,count2,0,i,0]=valid_dict[dictnames[i]][idx]
            except (ValueError,TypeError):
                pass
            count2=count2+1
        count1=count1+1
        dictlst_all.append(dictlst)
        excepts_all.append(excepts)
        tmp_date = tmp_date + timedelta(hours=6)

    # append to netcdf
    #print(M)
    nc.variables["stats_VHM0_altimeter"][:,:,:,:,2] = M[:,:,:,:,0]

    # close netcdf
    nc.close()


    # --- append some global attributes --- #
    nc = netCDF4.Dataset(os.path.join(outpath,\
        'product_quality_stats_ARCTIC_ANALYSIS_FORECAST_WAV_002_014_'
        + filedate.strftime('%Y')
        + filedate.strftime('%m')
        + '01-'
        + filedate.strftime('%Y') + filedate.strftime('%m')
        + str(calendar.monthrange(  filedate.year,
                                    filedate.month)[1]) + '.nc'),'r+')
    print ("\nAppending global attribute to netcdf validation file ...")
    globalAttribs = {}
    globalAttribs["product"] = "ARCTIC_ANALYSIS_FORECAST_WAV_002_014"
    nc.setncatts(globalAttribs)
    nc.sync()
    print ("Attribute appended")
    # --- adjust fill values --- #
    print ("\nAdjust _FillValue")
    plat = nc.variables['stats_VHM0_platform'][:]
    platnan = (np.where(np.isnan(plat)))
    if len(platnan[0])>0:
        print("NaNs found for platform data")
        for i in range(len(platnan[0])):
            plat[platnan[0][i],platnan[1][i],platnan[2][i],
                #platnan[3][i],platnan[4][i]] = 9999.
                platnan[3][i],platnan[4][i]] = 1e35
    alt = nc.variables['stats_VHM0_altimeter'][:]
    altnan = (np.where(np.isnan(alt)))
    if len(altnan[0])>0:
        print("NaNs found for altimeter data")
        for i in range(len(altnan[0])):
            alt[altnan[0][i],altnan[1][i],altnan[2][i],
                #altnan[3][i],altnan[4][i]] = 9999.
                altnan[3][i],altnan[4][i]] = 1e35
    nc.variables['stats_VHM0_platform'][:] = plat[:]
    nc.variables['stats_VHM0_altimeter'][:] = alt[:]
    nc.close()
    print ("fill values adjusted")


# --- Program Body -------------------------------------------------- #

create_monthly_nc(filedate,leadtimes,station_dict)

print('Monthly ARCMFC report file created')

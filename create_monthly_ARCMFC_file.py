#!/usr/bin/env python
import netCDF4
from datetime import datetime
import yaml
#from dateutil.relativedelta import relativedelta

"""
Some info
"""

now = datetime.now()
pm = now - relativedelta(months=1) # converts to previous month
if pm.month<10:
    timeplist=[str(pm.year)+ '0' +str(pm.month)]
else:
    timeplist=[str(pm.year) +str(pm.month)]

#timestr='2021 ' + pm.strftime("%b")
#timestrt='2021_' + pm.strftime("%b")
timestr='2021 Feb'
timestrt='2021_Feb'
timeplist=['202102']
print('time: '+timestr)

# plotpath
ppath = '/lustre/storeA/project/fou/om/waveverification/Arc-MFC/monthly/'+timestrt+'/'

# set color table for models

varname = 'Hs'
obs_all = []
mod_all = {'MWAM3':[]}
time_all = []

os.system('mkdir -p '+ppath)

for station, parameters in locations.iteritems():
    print(' ')
    print('verification of station '+station+' for '+timestr)


    obs_long = []
    mod_long = {'MWAM3':[]}


    for timep in timeplist: # loop over months
        print ' '
        print 'read data for station '+station+' for '+timep

        # open file
        path = '/lustre/storeA/project/fou/om/waveverification/data'

        year,month = int(timep[0:4]),int(timep[4:6])
        vf = validationfile(path,station,year,month)
        time = vf.time
        OBS  = vf.get_obs()
        if station=='draugen':
            time_all = time_all + list(time)



    # Specify which WM sensor to use for validation
        try:
            sensor = bestWMsensor[station]
        except KeyError:
            sensor = 0

        obsraw = OBS[varname][sensor]
        try:
            obs = obsraw.data
            obs[obsraw.mask==True] = sp.nan # make sure all masked values are nan 
        except AttributeError:
            obs = obsraw
        units = vf.nc.variables[varname+'_OBS'].units

        if all(sp.isnan(obs.data)):
            print('no data for '+station+' during '+timestr)
            continue

        # select variable from  each model:
        modeldata = select_var_from_models(vf,varname)
        obs_long.append(obs)
        for gname, var in modeldata.iteritems():
            if gname in mod_long.keys():
                mod_long[gname].append(var)

    # make arrays from lists
    obs_long = np.concatenate(obs_long)
    mod_longa={}
    for mod in mod_long.keys():
        mod_longa[mod] = np.concatenate(mod_long[mod],axis=1)


    # append to list for all stations:
    obs_all.append(obs_long)
    for gname, var in modeldata.iteritems():
        if gname in mod_all.keys():
            print('append ' +gname+ ' for ' + station)
            mod_all[gname].append(mod_longa[gname])

# make arrays from list
obs = np.array(obs_all)
modeldata = {}
for gname in mod_all.keys():
    modeldata[gname] = np.dstack(mod_all[gname])


var = modeldata['MWAM3'].transpose(2,1,0)

print('var.shape ', var.shape)
print('obs.shape ', obs.shape)

#
# compute statistics
#

# reshape time axis to join hours
nhours = 6

obsS = obs.reshape(obs.shape[0],nhours,obs.shape[1]/nhours)
varS = var.reshape(var.shape[0],nhours,var.shape[1]/nhours,var.shape[2])

time = time_all[::6]
timeunit = "days since 2001-01-01 12:00:00 UTC"
time_start = time[0].strftime('%Y%m%d')
time_end = time[-1].strftime('%Y%m%d')
print(time_start, time_end)

# produce netcdf file:
#nc = netCDF4.Dataset(os.path.join(ppath,'product_quality_stats_ARCTIC_ANALYSIS_FORECAST_WAV_002_006_'+time_start+'-'+time_end+'_test_region.nc'),'w')
nc = netCDF4.Dataset(os.path.join(ppath,'product_quality_stats_ARCTIC_ANALYSIS_FORECAST_WAV_002_006_'+time_start+'-'+time_end+'.nc'),'w')
nc.contact = 'patrikb@met.no'
nc.product = 'Arctic wave model WAM'
nc.production_centre = 'Arctic MFC'
nc.production_unit = 'Norwegian Meteorological Institute'
nc.creation_date = str(dt.datetime.now())
nc.thredds_web_site = 'http://thredds.met.no/thredds/myocean/ARC-MFC/mywave-arctic.html'

ncdims = {'string_length':28, 'areas':3, 'metrics':4, 'surface':1, 'forecasts':10} # and time, unlim
metric_names = [name.ljust(28) for name in ["mean of product", "mean of reference", "mean square difference", "number of data values"]]


nc.createDimension('time',size=None)
for name,dim in ncdims.iteritems():
    nc.createDimension(name,size=dim)

nc_time = nc.createVariable('time','f8',dimensions=('time'))
nc_time[:] = netCDF4.date2num(time,units=timeunit)
nc_time.units = timeunit
nc_time.long_name = 'validity time'

nc_metricnames = nc.createVariable('metric_names','S1', dimensions=(u'metrics',u'string_length'))
nc_metricnames[:] = netCDF4.stringtochar(np.array(metric_names))

nc_areanames = nc.createVariable('area_names','S1', dimensions=(u'areas',u'string_length'))
nc_areanames[0] = netCDF4.stringtochar(np.array('North Sea and Norwegian Sea'.ljust(28)))
nc_areanames[1] = netCDF4.stringtochar(np.array('Full domain                '.ljust(28)))
nc_areanames[2] = netCDF4.stringtochar(np.array('Nordic Seas              '.ljust(28)))
nc_areanames.long_name = 'area names'
nc_areanames.description = 'region over which statistics are aggregated'

nc_leadtime = nc.createVariable('forecasts','f4',dimensions=('forecasts'))
nc_leadtime.long_name = 'forecast lead time'
nc_leadtime.units = 'hours'
nc_leadtime[:] = sp.arange(12,229,24)


varArcMFCname = {'Hs': 'stats_VHM0'}
varstandardname = {'Hs':'sea_surface_wave_significant_height'}

ncvar = nc.createVariable(varArcMFCname[varname],'f4', dimensions=('time', 'forecasts', 'surface', 'metrics', 'areas'), fill_value=9999.)
ncvar.standard_name = varstandardname[varname]
ncvar.parameter = varArcMFCname[varname]
ncvar.units = 'm'
ncvar.reference_source = 'wave data from offshore platforms available from d22 files at the Norwegian Meteorological Institute'

# calculate statistics (bias and root-mean-square difference)

for leadtime in range(10):
    # mean of product
    ncvar[:,leadtime,0,0,0] = sp.array([sp.mean( vt.returnclean(obsS[:,:,i],varS[:,:,i,leadtime])[1]) for i in range(obsS.shape[2])])
    # mean of reference
    ncvar[:,leadtime,0,1,0] = sp.array([sp.mean( vt.returnclean(obsS[:,:,i],varS[:,:,i,leadtime])[0]) for i in range(obsS.shape[2])])
    # mean square difference
    ncvar[:,leadtime,0,2,0] = sp.array([vt.msd( *vt.returnclean(obsS[:,:,i],varS[:,:,i,leadtime])) for i in range(obsS.shape[2])])
    # number of data values
    ncvar[:,leadtime,0,3,0] = sp.array([ len(vt.returnclean(obsS[:,:,i],varS[:,:,i,leadtime])[1]) for i in range(obsS.shape[2])])

nc.close()


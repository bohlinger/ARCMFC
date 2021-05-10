# --- imports --- #

# standard
import yaml
import numpy as np
from datetime import datetime,timedelta
import os
import argparse
from argparse import RawTextHelpFormatter
import netCDF4

# custom
from satmod import satellite_class
from modelmod import model_class
from collocmod import validate_collocated_values
from utils import system_call, make_pathtofile, get_pathtofile
from ncmod import dumptonc_stats

# --- parser --- #
parser = argparse.ArgumentParser(
    description="""
Validate collocated data from satellite and wave model,\n
and dump data to monthly nc-file.
If file exists, data is appended.

Usage:
./validate_sat.py -sd 2021010100 -ed 2021013123 -sat all
    """,
    formatter_class = RawTextHelpFormatter
    )
parser.add_argument("-sd", metavar='startdate',
    help="start date of time period")
parser.add_argument("-ed", metavar='enddate',
    help="end date of time period")
parser.add_argument("-var", metavar='varname',
    help="variable name")
parser.add_argument("-sat", metavar='satname',
    help="satellite name")
parser.add_argument("-model", metavar='modelname',
    help="model name")
parser.add_argument("-region", metavar='region',
    help="region name")
parser.add_argument("-lt", metavar='leadtime',
    help="leadtime")
parser.add_argument("-twin", metavar='timewindow',
    help="time limit for collocation")

args = parser.parse_args()

now = datetime.now()
if args.sd is None:
    args.sd = datetime(now.year,now.month,now.day,0)-timedelta(days=1)
else:
    args.sd = datetime(int(args.sd[0:4]),int(args.sd[4:6]),
                int(args.sd[6:8]),int(args.sd[8:10]))
if args.ed is None:
    args.ed = datetime(now.year,now.month,now.day)-timedelta(minutes=1)
else:
    args.ed = datetime(int(args.ed[0:4]),int(args.ed[4:6]),
                int(args.ed[6:8]),int(args.ed[8:10]))-timedelta(minutes=1)

if args.var is None:
    args.var = 'Hs'

if args.model is None:
    args.model = 'ARCMFC3'

if args.lt is None:
    args.lt = 0

if args.twin is None:
    args.twin = 30

if (args.sat is None):
    args.sat = 's3a'

if args.region is None:
    args.region = args.model

print(args)

print( '# Start process of validating satellite vs wave model data'
        + ' and dump to nc-file #')

# --- prerequisites --- #

# find wavy path
tmppath = str(system_call('echo $PYTHONPATH'))[2:-3]
wavydir = [s for s in tmppath.split(":") if 'wavy' in s][0]

configdir = os.path.abspath(os.path.join(wavydir,
                                         '..',
                                         'config/'))
with open(configdir+'/collocation_specs.yaml','r') as stream:
    collocation_dict=yaml.safe_load(stream)

inpath_template = collocation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['path_template']
infile_template = collocation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['file_template']
instrsublst = collocation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['strsub']
intmppathlst = [p + ('/' + infile_template) for p in inpath_template]

with open(configdir+'/validation_specs.yaml','r') as stream:
    validation_dict=yaml.safe_load(stream)

outpath_template = validation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['path_template']
outfile_template = validation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['file_template']
outstrsublst = validation_dict['path']['satellite_altimeter']\
                         ['local']['nc']['strsub']
outtmppath = outpath_template + '/' + outfile_template

# settings
leadtimes = [0, 12, 36, 60, 84, 108, 132, 156, 180, 204, 228]

# --- program body --- #
tmpdate = args.sd
while tmpdate <= args.ed:
    for lt in leadtimes:
        leadtimestr="{:0>3d}h".format(lt)
#        for i in range(1):
        try:
            print('DATE: ',tmpdate)
            print('LEADTIME: ',lt)
            # read collocated data
            inpathtofile = get_pathtofile(intmppathlst,
                                        instrsublst,
                                        tmpdate,
                                        varalias=args.var,
                                        model=args.model,
                                        mission=args.sat,
                                        region=args.region,
                                        leadtime=leadtimestr)
            nc = netCDF4.Dataset(inpathtofile,mode='r')
            mods = np.array(nc.variables['model_values'])
            mods[mods>30] = np.nan
            mods[mods<0] = np.nan
            obs = np.array(nc.variables['obs_values'])
            obs[obs>30] = np.nan
            obs[obs<0] = np.nan
            time = nc.variables['time']
            time_unit = time.units
            dtime_tmp = netCDF4.num2date(time[:],time.units)
            dtime = [datetime(dt.year,dt.month,dt.day,
                    dt.hour,dt.minute,dt.second) for dt in dtime_tmp]
            nc.close()
            # validate
            validation_dict = validate_collocated_values(\
                                mods=mods,obs=obs,dtime=dtime,\
                                target_t=[tmpdate],twin=args.twin)
            # dump to nc-file
            title='validation file'
            outpathtofile = make_pathtofile(outtmppath,
                                        outstrsublst,
                                        tmpdate,
                                        varalias=args.var,
                                        model=args.model,
                                        mission=args.sat,
                                        region=args.region,
                                        leadtime=leadtimestr)
            # --- write to nc --- #
            dumptonc_stats(outpathtofile,title,tmpdate,time_unit,
                            validation_dict)
        except Exception as e:
            print('No validation!')
            print(e)
    tmpdate = tmpdate + timedelta(hours=12)

print( '# Finished process of validating satellite vs wave model'
        + ' and dump to nc-file #')

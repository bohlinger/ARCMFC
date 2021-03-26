# --- imports --- #

# standard
import yaml
import numpy as np
from datetime import datetime,timedelta
import os
import argparse
from argparse import RawTextHelpFormatter

# custom
from stationmod import station_class
from utils import system_call

# --- parser --- #
parser = argparse.ArgumentParser(
    description="""
Retrieve data from in-sistu stations, collocate with model,\n 
and dump data to monthly nc-file.
If file exists, data is appended.

Usage:
./collocate_stat.py -sd 2021010100 -ed 2021013123 -stat all
    """,
    formatter_class = RawTextHelpFormatter
    )
parser.add_argument("-sd", metavar='startdate',
    help="start date of time period")
parser.add_argument("-ed", metavar='enddate',
    help="end date of time period")
parser.add_argument("-var", metavar='varname',
    help="variable name")
parser.add_argument("-station", metavar='stationname',
    help="station name")
parser.add_argument("-sensor", metavar='sensorname',
    help="sensor name")
parser.add_argument("-model", metavar='modelname',
    help="model name")
parser.add_argument("-lt", metavar='leadtime',
    help="leadtime")
parser.add_argument("-dist", metavar='distance',
    help="distance limit for collocation")

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
                int(args.ed[6:8]),int(args.ed[8:10]))

if args.var is None:
    args.var = 'Hs'

if args.model is None:
    args.model = 'mwam4'

if args.lt is None:
    args.lt = 0

if args.dist is None:
    args.dist = 6

print(args)

print( '# Start process of collecting platform'
        + ' data, collocate with model,\n'
        + ' and dump to nc-file #')

# --- prerequisites --- #

# find wavy path
tmppath = str(system_call('echo $PYTHONPATH'))[2:-3]
wavydir = [s for s in tmppath.split(":") if 'wavy' in s][0]

# get variable info
configdir = os.path.abspath(os.path.join(wavydir, '..', 'config/station_specs.yaml'))
with open(configdir,'r') as stream:
    station_dict=yaml.safe_load(stream)

# settings
if (args.station is None or args.station == 'all'):
    platformlst = station_dict['platform'].keys()
else:
    platformlst = [args.station]

date_incr = 1

# --- program body --- #
for station in platformlst:
    for sensor in station_dict['platform'][station]['sensor']:
        print('station:',station,'; with sensor:',sensor)
        st_obj = station_class(station,sensor,args.sd,args.ed,
                                   varalias=args.var)
        col_obj = collocation_class(model=model,st_obj=st_obj,distlim=dist,
                                    leadtime=args.lt,date_incr=data_incr)
        # --- write to nc --- #
        col_obj.write_to_monthly_nc()

print( '# Finished process of collecting platform'
        + ' data, collocate with model,\n'
        + ' and dump to nc-file #')










#statname = 'ekofiskL'
#sensor = 'waverider'
#varalias = 'Hs'
#sd = datetime(2020,12,1)
#ed = datetime(2020,12,3,23)
#
#st_obj = station_class('ekofiskL','waverider',sd,ed,varalias=varalias)
#
#model = 'mwam4'
#col_obj = collocation_class(model=model,st_obj=st_obj,distlim=6,date_incr=1)
#
#import matplotlib.pyplot as plt
#plt.plot(st_obj.vars['datetime'],st_obj.vars['sea_surface_wave_significant_height'],'k--')
#plt.plot(col_obj.vars['datetime'],col_obj.vars['obs_values'],'ko')
#plt.plot(col_obj.vars['datetime'],col_obj.vars['model_values'],'rx')
#plt.show()

# --- imports --- #

# standard
import yaml
import numpy as np
from datetime import datetime,timedelta
import os
import argparse
from argparse import RawTextHelpFormatter

# custom
from satmod import satellite_class
from modelmod import model_class
from collocmod import collocation_class
from utils import system_call

# --- parser --- #
parser = argparse.ArgumentParser(
    description="""
Retrieve data from satellite altimeter, collocate with model,\n 
and dump data to monthly nc-file.
If file exists, data is appended.

Usage:
./collocate_sat.py -sd 2021010100 -ed 2021013123 -sat all
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
parser.add_argument("-dist", metavar='distance',
    help="distance limit for collocation")
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

if args.dist is None:
    args.dist = 6

if args.twin is None:
    args.twin = 30

if (args.sat is None):
    args.sat = 's3a'

if args.region is None:
    args.region = args.model

print(args)

print( '# Start process of collecting satellite'
        + ' data, collocate with model,\n'
        + ' and dump to nc-file #')

# --- prerequisites --- #

# find wavy path
tmppath = str(system_call('echo $PYTHONPATH'))[2:-3]
wavydir = [s for s in tmppath.split(":") if 'wavy' in s][0]

# get variable info
configdir = os.path.abspath(os.path.join(wavydir, 
                                         '..', 
                                         'config/satellite_specs.yaml'))
with open(configdir,'r') as stream:
    satellite_dict=yaml.safe_load(stream)

# settings
leadtimes = [0, 12, 36, 60, 84, 108, 132, 156, 180, 204, 228]
#leadtimes = [132]

# --- program body --- #
tmpdate = args.sd
while tmpdate <= args.ed:
    sd = tmpdate
    ed = tmpdate
    sa_obj = satellite_class(sdate=sd,region=args.region,
                             sat=args.sat, varalias=args.var,
                             twin=args.twin)
    for lt in leadtimes:
        try:
            print('DATE: ',tmpdate)
            print('LEADTIME: ',lt)
            mc_obj = model_class(fc_date=sd,varalias=args.var,
                                model=args.model,leadtime=lt)
            if 'col_obj' in locals():
                col_obj = collocation_class(mc_obj=mc_obj,sa_obj=sa_obj,
                                    distlim=args.dist,leadtime=lt,
                                    col_obj=col_obj)
            else:
                col_obj = collocation_class(mc_obj=mc_obj,sa_obj=sa_obj,
                                    distlim=args.dist,leadtime=lt)
            # --- write to nc --- #
            col_obj.write_to_monthly_nc()
        except Exception as e:
            print('No collocation!')
            print(e)
    if 'col_obj' in locals():
        del col_obj
    tmpdate = tmpdate + timedelta(hours=12)

print( '# Finished process of collecting satellite'
        + ' data, collocate with model,\n'
        + ' and dump to nc-file #')

# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:34:18 2021

@author: ormondt
"""

import os
import pandas as pd
import numpy as np
import datetime

import cht.misc.fileops as fo

def merge_timeseries(path, model_name, model_region, model_type, station, t0=None, t1=None,
                     prefix='waterlevel',
                     resample=None):
    
    if prefix == "waterlevel":
        name_str = "wl"
    else:
        name_str = prefix
        
    available_times = []    
    cycle_list = fo.list_folders(os.path.join(path,'*z'))
    for it, cycle_string in enumerate(cycle_list):
        available_times.append(datetime.datetime.strptime(cycle_list[it][-12:],"%Y%m%d_%Hz"))

    if t0==None or t1==None:
        t0 = available_times[0]
        t1 = available_times[-1]
            
    # New pandas series
    wl=[]
    idx=[]
    wl.append(0.0)
    idx.append(pd.Timestamp("2100-01-01"))
    vv = pd.Series(wl, index=idx)
    vv.index.name = "date_time"
    vv.name       = name_str
    
    okay = False
    
    for it, t in enumerate(available_times):
       
        if t>=t0 and t<=t1:       
            
            csv_file = os.path.join(path,
                                    cycle_list[it][-12:],
                                    model_region,
                                    model_type,
                                    model_name,
                                    prefix + "." + station + ".csv")
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, header=0,
                                 index_col=0,
                                 parse_dates=True).squeeze()
                df.index.name = "date_time"
                df.name       = name_str
                
                okay = True
                # df            = df.resample('T').mean()
                # df            = df.interpolate(method='time')
                
                
                # Find last time in merged time series that is smaller than first time in new timeseries
                ilast = np.where(vv.index<df.index[0])[-1]
                if ilast.any():
                    ilast = ilast[-1]
                    vv = vv[0:ilast]
                    vv = vv.append(df)
                else:
                    vv = df
                    
    if okay:                                    
        
        if resample:                
    
            from scipy import interpolate
            
            t0 = (vv.index - vv.index[0]).total_seconds()
            t1 = np.arange(0.0,t0[-1], resample)
            f  = interpolate.interp1d(t0, vv)
            v1 = f(t1)
            t1 = vv.index[0] + t1*datetime.timedelta(seconds=1)
            
            vv = pd.Series(v1, index=t1)
            vv.index.name = "date_time"
            vv.name       = name_str
                        
    if okay:                                    
        return vv                
    else:
        return None
 
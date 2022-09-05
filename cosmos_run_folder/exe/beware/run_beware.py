# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 18:06:47 2022

@author: wcp_w2111151
"""
#import sys

from cht.beware import BEWARE
from cht.vo21 import runup_vo21
import os
import pandas as pd
import numpy as np
import mat73
import xarray as xr
import datetime
import pathlib

exefolder = str(pathlib.Path(__file__).parent.resolve())
bwDatabase = os.path.join(exefolder, 'XBeach_BEWARE_database.nc')

print("Exe folder : " + exefolder)

bw=BEWARE('beware.inp')
# runfolder = bw.input.folder
tstart = (bw.input.tstart - bw.input.tref)
tstop  = (bw.input.tstop - bw.input.tref)

# Read the profile files
df = pd.read_csv('beware.profs', index_col=False,
     delim_whitespace=True) 
allprofs= df.profid.values
types= df.coasttype.values
x=df.x_off.values
y=df.y_off.values
xc=df.x_coast.values
yc=df.y_coast.values

profdata=mat73.loadmat('profile_characteristics.mat')
profid= profdata['profid'].astype(int)     

# Read forcing files
hs= pd.read_csv('beware.bhs', index_col=0, header=None,
                  delim_whitespace=True)
tp= pd.read_csv('beware.btp', index_col=0, header=None,
                  delim_whitespace=True)
wl= pd.read_csv('beware.bzs', index_col=0, header=None,
                  delim_whitespace=True)

# Interpolate to required time intervals
hs.index=pd.to_timedelta(hs.index, unit="s")
hs = hs.resample(bw.input.dT).interpolate(method='time')
indexes = hs[(hs.index<tstart) | (hs.index>=tstop)].index
hs.drop(indexes, inplace=True)

tp.index=pd.to_timedelta(tp.index, unit="s")
tp = tp.resample(bw.input.dT).interpolate(method='time')
indexes = tp[(tp.index<tstart) | (tp.index>=tstop)].index
tp.drop(indexes, inplace=True)

wl.index=pd.to_timedelta(wl.index, unit="s")
wl = wl.resample(bw.input.dT).interpolate(method='time')
indexes = wl[(wl.index<tstart) | (wl.index>=tstop)].index
wl.drop(indexes, inplace=True)

# Pre-allocate output
if bw.input.runup:
    R2_tot, R2_setup, R2_wl =np.zeros(np.shape(hs)), np.zeros(np.shape(hs)), np.zeros(np.shape(hs))
if bw.input.flooding:
    hmoig, tpig, scale, nswl =np.zeros(np.shape(hs)), np.zeros(np.shape(hs)), np.zeros(np.shape(hs)), np.zeros(np.shape(hs))
bwid, bwprof, bwslope, allid = [], [], [], []

for iprof, prof in enumerate(allprofs):
    ID= types[iprof]
       
    ID2= np.argwhere(prof == profid)[0]
    print(iprof)
    if ID==1: # SANDY
        sl1={}
        sl1['z']= np.flip(profdata['depth'][ID2[0]])
        sl1['x']= np.arange(0, len(sl1['z'])*2,2)
        sl2 = profdata['beachslope'][ID2[0]]
        vo=runup_vo21(hs.values[:,iprof],tp.values[:,iprof], wl.values[:,iprof], sl1, sl2, 'xz')
        vo.compute_r2p(0, 0)
        if bw.input.runup:
            R2_tot[:,iprof]= vo.r2p + vo.ztide
            R2_setup[:,iprof]= vo.setup
            R2_wl[:,iprof] = vo.ztide
        if bw.input.flooding:    
            hmoig[:,iprof]= vo.IG
            tpig[:,iprof]=vo.tm0_ig
            nswl[:,iprof]= vo.setup
       
    elif ID==2: # REEF
        bwid.append(iprof)
        bwprof.append(prof.astype(int))
        bwslope.append(profdata['beachslope'][ID2[0]])

# Adjust input conditions to BEWARE limits
bwhs= hs.values[:,bwid]
bwhs= np.where(bwhs==-999, np.nan, bwhs)
bwhs= np.where(bwhs<=1, 1.01, bwhs)
bwhs= np.where(bwhs>=10, 9.99, bwhs)

bwtp= tp.values[:,bwid]
bwtp= np.where(bwtp==-999, np.nan, bwtp)
bwtp= np.where(bwtp<=6, 6.01, bwtp)
bwtp= np.where(bwtp>=22, 21.99, bwtp)

bwtp= np.where(np.logical_and(bwhs>3, bwtp<=8), 8.01, bwtp) # adjust for steepness
bwtp= np.where(np.logical_and(bwhs>7, bwtp<=10), 10.01, bwtp) # adjust for steepness


bwwl= wl.values[:,bwid]
bwwl= np.where(bwwl==-999, np.nan, bwwl)
bwwl= np.where(bwwl<=0, 0.01, bwwl)
bwwl= np.where(bwwl>=4, 3.99, bwwl)

bwslope=  np.where(np.array(bwslope)<=0.05, 0.0501, np.array(bwslope))
bwslope=  np.where(bwslope>=0.2, 0.199, bwslope)

# Run BEWARE
bw.run(bwhs, bwtp, bwwl, bwslope, bwprof,
       bwDatabase, match_runup= r'match_runup.mat', match_flooding= r'match_flooding.mat')

if bw.input.runup:
    R2_tot[:,bwid]= np.transpose(bw.out['R2_tot'])
    R2_setup[:,bwid]= np.transpose(bw.out['R2_setup'])
    R2_wl[:,bwid]= np.transpose(bw.out['R2_wl'])
if bw.input.flooding:
    hmoig[:,bwid]=  4*np.sqrt(np.transpose(bw.out['m0']))
    tpig[:,bwid]= 1/np.transpose(bw.out['fp'])
    # scale[:, bwid]=np.transpose(bw.out['scale'])
    nswl[:, bwid]=np.transpose(bw.out['setup'])
    
ts =pd.to_timedelta(hs.index, unit="s").total_seconds()+(bw.input.tref-datetime.datetime(1970,1,1)).total_seconds()
sp=[]
if bw.input.runup:
    sp.append(xr.DataArray(data=np.transpose(R2_tot),     name=r"R2_tot",   dims=["prof", "t"]))
    sp.append(xr.DataArray(data=np.transpose(R2_setup),   name=r"R2_set",   dims=["prof", "t"]))
    sp.append(xr.DataArray(data=np.transpose(R2_wl),      name=r"R2_wl",    dims=["prof", "t"]))
if bw.input.flooding:
    sp.append(xr.DataArray(data=np.transpose(hmoig),      name=r"obs_hm0_ig",   dims=["prof", "t"]))
    sp.append(xr.DataArray(data=np.transpose(tpig),       name=r"obs_tpig",     dims=["prof", "t"]))
    # sp.append(xr.DataArray(data=scale,      name=r"scale",    dims=["prof", "t"]))
    sp.append(xr.DataArray(data=np.transpose(nswl),      name=r"obs_setup",    dims=["prof", "t"]))

sp.append(xr.DataArray(data=allprofs,       name=r"Profiles", dims=["prof"]))
sp.append(xr.DataArray(data= ts,            name=r"time",    attrs = dict(long_name = "time_in_seconds_since_1970-01-01 00:00:00"),
                       dims=["t"], coords=dict(reference_time=datetime.datetime(1970,1,1)) ))
sp.append(xr.DataArray(data= bw.input.tref, name =r'reference_t'))
sp.append(xr.DataArray(data=types,          name=r"coasttypes",  dims=["prof"]))

sp.append(xr.DataArray(data=np.transpose(hs.values),   name=r"Hs",      dims=["prof", "t"]))
sp.append(xr.DataArray(data=np.transpose(tp.values),   name=r"Tp",      dims=["prof", "t"]))
sp.append(xr.DataArray(data=np.transpose(wl.values),   name=r"WL",      dims=["prof", "t"]))

sp.append(xr.DataArray(data=x,   name=r"x_off",      dims=["prof"]))
sp.append(xr.DataArray(data=y,   name=r"y_off",      dims=["prof"]))

sp.append(xr.DataArray(data=xc,   name=r"x_coast",      dims=["prof"]))
sp.append(xr.DataArray(data=yc,   name=r"y_coast",      dims=["prof"]))

savedata= xr.merge(sp)

savename= r"BW_output.nc"
savedata.to_netcdf(path= savename)
savedata.close()

# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:28:58 2021

@author: ormondt
"""
import os
from pyproj import CRS
import numpy as np
import datetime

from .cosmos import cosmos
from cht.tropical_cyclone.tropical_cyclone import TropicalCycloneEnsemble
from cht.meteo.meteo import filter_cyclones_TCvitals
from datetime import datetime

def setup_track_ensemble():
    # Check if scenario is forced with track files or gridded data
    if not cosmos.scenario.meteo_track:
        # If only gridded data, try to extract the storm track
        # Use only the first meteo_subset for now

        for meteo_subset in cosmos.meteo_subset:
            if meteo_subset.name == cosmos.scenario.meteo_dataset:
                break

#        meteo_subset = cosmos.meteo_subset[0]
        tracks = meteo_subset.find_cyclone_tracks()
#        # Filter cyclone based on TCvitals
#        tracks = filter_cyclones_TCvitals(tracks)
        # Take the one with the longest track (this is of course bullshit)
        imax = 0
        for itrack, track in enumerate(tracks):
            if len(track.track) > imax:
                itrmax = itrack
                imax = len(track.track)

        # Use the first track to make ensembles
        tc = tracks[itrmax]
        tc.account_for_forward_speed()
        tc.estimate_missing_values()
        tc.include_rainfall = True

        # Write *.cyc file
        tc.write_track("laura.cyc", "ddb_cyc")
    else:
        # Read in storm track from *.cyc file
        tc = tc.read(cosmos.scenario.meteo_track)    
    # Generate track ensemble
    cosmos.scenario.track_ensemble = TropicalCycloneEnsemble(TropicalCyclone=tc)
    t0str = tc.track.loc[0]["datetime"]
    t1str = tc.track.loc[len(tc.track) - 1]["datetime"]
    cosmos.scenario.track_ensemble.tstart  = datetime.strptime(t0str, "%Y%m%d %H%M%S")
    cosmos.scenario.track_ensemble.tend    = datetime.strptime(t1str, "%Y%m%d %H%M%S")
    cosmos.scenario.track_ensemble.compute_ensemble(number_of_realizations=cosmos.scenario.track_ensemble_nr_realizations)    

    # Get outline of ensemble
    gdf = cosmos.track_ensemble.get_outline(buffer=300000.0)

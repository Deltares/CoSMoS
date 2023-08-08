# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:28:58 2021

@author: ormondt
"""
import os
from pyproj import CRS
import numpy as np
import datetime
import shapely
import copy

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

        tc.spiderweb_radius = 400.0
        tc.nr_radial_bins   = 100

        # Write *.cyc file
        tc.write_track("laura.cyc", "ddb_cyc")
    else:
        # Read in storm track from *.cyc file
        from cht.tropical_cyclone.tropical_cyclone import TropicalCyclone
        tc= TropicalCyclone()
        cyc_file = os.path.join(cosmos.config.meteo_database.path, "tracks", cosmos.scenario.meteo_track + ".cyc")
        tc.from_ddb_cyc(cyc_file)
        tc.account_for_forward_speed()
        tc.estimate_missing_values()
        tc.include_rainfall = True

    # Generate track ensemble
    cosmos.scenario.track_ensemble = TropicalCycloneEnsemble(TropicalCyclone=tc)
    cosmos.scenario.track_ensemble.tstart           = cosmos.scenario.ref_date
    cosmos.scenario.track_ensemble.tstart_ensemble  = cosmos.scenario.cycle
    cosmos.scenario.track_ensemble.tend             = cosmos.stop_time
    cosmos.scenario.track_ensemble.include_best_track = 1
    cosmos.scenario.track_ensemble.compute_ensemble(number_of_realizations=cosmos.scenario.track_ensemble_nr_realizations)    

    # Write to files
    cosmos.scenario.track_ensemble.to_cyc(cosmos.scenario.cycle_track_ensemble_cyc_path)
    cosmos.scenario.track_ensemble.to_spiderweb(cosmos.scenario.cycle_track_ensemble_spw_path)
    cosmos.scenario.track_ensemble.to_shapefile(cosmos.scenario.cycle_track_ensemble_path)

    # Get outline of ensemble
    cone = cosmos.scenario.track_ensemble.get_outline(buffer=300000.0)
    
    # Loop through all models and check if they fall within cone
    models_to_add = []
    for model in cosmos.scenario.model:
        if model.type == 'beware' or shapely.intersects(cone.loc[0]["geometry"], model.outline.loc[0]["geometry"]):
            # Add model
            ensemble_model = copy.deepcopy(model)
            ensemble_model.name = model.name + "_ensemble"
            ensemble_model.ensemble = True
            if ensemble_model.flow_nested_name:
                ensemble_model.flow_nested_name += "_ensemble"
            if ensemble_model.wave_nested_name:
                ensemble_model.wave_nested_name += "_ensemble"
            if ensemble_model.bw_nested_name:
                ensemble_model.bw_nested_name += "_ensemble"

            # # Delete meteo subsets from models (for memory)
            # ensemble_model.meteo_subset = None
            # for nested_list in [ensemble_model.wave_nested, ensemble_model.flow_nested, ensemble_model.bw_nested]:
            #     if nested_list:
            #         try:
            #             for nested_item in nested_list:
            #                 nested_item.meteo_subset = None
            #         except:
            #             nested_list.meteo_subset = None
            # Set initial run status to 
            models_to_add.append(ensemble_model)

    cosmos.scenario.model = cosmos.scenario.model  + models_to_add
    
    # Get list of models that have already finished
    finished_list = os.listdir(cosmos.scenario.cycle_job_list_path)

    for model in models_to_add:
        model.get_nested_models()
        model.set_paths()

        # Check (again) for models if they are finished
        model.status = "waiting"
        # Check finished models
        for file_name in finished_list:
            model_name = file_name.split('.')[0]
            if model.name.lower() == model_name.lower():
                model.status = "finished"
                model.run_simulation = False
                break            
        if model.priority == 0:
            model.run_simulation = False
    
    if cosmos.config.cycle.only_run_ensembles:
        # Remove all models that are not ensembles       
        cosmos.scenario.model = [model for model in cosmos.scenario.model if model.ensemble]

    # Set ensemble names
    cosmos.scenario.ensemble_names = []
    for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
        cosmos.scenario.ensemble_names.append(str(iens+1).zfill(5))
    cosmos.scenario.best_track = str(0).zfill(5)


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

from .cosmos_main import cosmos
from cht_cyclones.tropical_cyclone import TropicalCycloneEnsemble
from cht_meteo.meteo import filter_cyclones_TCvitals, find_priorityTC
import cht_utils.fileops as fo
from datetime import datetime
import cht_utils.misc_tools

def setup_track_ensemble():

    tc = None

    # Check if scenario is forced with track files or gridded data
    if not cosmos.scenario.meteo_track:
        # If only gridded data, try to extract the storm track
        # Use only the first meteo_subset for now

        for meteo_subset in cosmos.meteo_subset:
            if meteo_subset.name == cosmos.scenario.meteo_dataset:
                break

        cosmos.log("Finding storm tracks ...")
        tracks = meteo_subset.find_cyclone_tracks(method="vorticity",
                                                  pcyc=100000.0,
                                                  vcyc=40.0,
                                                  vmin=18.0,
                                                  dt = 3)
        # Filter cyclone based on TCvitals
        # Use coordinates specified in meteo file to extract nearest track from gridded meteo data (if present)
        if hasattr(cosmos.scenario, 'meteo_lon'): 
            meteo_lon = cosmos.scenario.meteo_lon
            meteo_lat = cosmos.scenario.meteo_lat
        else:
            meteo_lon = None
            meteo_lat = None

        tc = find_priorityTC(tracks, "priority_storm.txt", meteo_lon, meteo_lat)
#        tc = tracks[0]

        # Use the first track to make ensembles
        tc.account_for_forward_speed()
        tc.estimate_missing_values()
        tc.include_rainfall = True


    else:
        # Read in storm track from *.cyc file
        from cht_cyclones.tropical_cyclone import TropicalCyclone
        tc = TropicalCyclone()

        # check if absolute path is given
        if not os.path.isabs(cosmos.scenario.meteo_track):
            filename = os.path.join(cosmos.config.meteo_database.path, "tracks", cosmos.scenario.meteo_track + ".cyc")
        else:
            filename = cosmos.scenario.meteo_track
        
        # convert to tc based on file extension
        if filename.endswith(".cyc"):
            tc.from_ddb_cyc(filename)
        elif filename.endswith(".trk"):
            tc.from_trk(filename)
        else:
            cosmos.log("Unknown track file format: " + filename)
            return

        if len(tc.track) < 2:
            cosmos.log("Track too short: " + filename)
            return

        tc.account_for_forward_speed()
        tc.estimate_missing_values()
        tc.include_rainfall = True  

    if not tc:
        # No track found
        return
    
    if len(tc.track) < 3:
        # Track too short
        return

    # Set radius and number of radial bins 
    tc.spiderweb_radius = 400.0
    tc.nr_radial_bins   = 100

    # Generate track ensemble
    cosmos.log("Generating track ensemble ...")
#    cosmos.scenario.ensemble = True
    cosmos.scenario.cyclone_track = tc.track
    cosmos.scenario.track_ensemble = TropicalCycloneEnsemble(TropicalCyclone=tc)
    cosmos.scenario.track_ensemble.position_method = 1
    # NOTE this could be before, after best-track meteo data, so why would we do this?
    if cosmos.scenario.track_ensemble.tstart < cosmos.scenario.ref_date:
        cosmos.scenario.track_ensemble.tstart = cosmos.scenario.ref_date
    if cosmos.scenario.track_ensemble.tend > cosmos.stop_time:
        cosmos.scenario.track_ensemble.tend = cosmos.stop_time
    cosmos.scenario.track_ensemble.include_best_track = 1

    # Set the ensemble start time, always equal to the cycle time
    # NOTE: when tc starts later than cycle, ensemble also starts to deviate later
    cosmos.scenario.track_ensemble.tstart_ensemble  = cosmos.cycle.replace(tzinfo=None)

    cosmos.scenario.track_ensemble.dt = 3
    cosmos.scenario.track_ensemble.compute_ensemble(number_of_realizations=cosmos.scenario.track_ensemble_nr_realizations)    

    # Write to files
    cosmos.log("Saving track files ...")
    cosmos.scenario.track_ensemble.to_cyc(cosmos.scenario.cycle_track_ensemble_cyc_path)
    cosmos.log("Saving spiderweb files ...")
    cosmos.scenario.track_ensemble.to_spiderweb(cosmos.scenario.cycle_track_ensemble_spw_path)
    cosmos.scenario.track_ensemble.to_shapefile(cosmos.scenario.cycle_track_ensemble_path)
    
    # Get outline of ensemble
    cone = cosmos.scenario.track_ensemble.get_outline(buffer=200000.0)

    # Make geojson file (in webviewer folder)
    file_name = os.path.join(cosmos.config.webviewer.data_path,
                           cosmos.scenario.name,
                           cosmos.cycle_string,
                           "track_ensemble.geojson.js")
    cosmos.scenario.track_ensemble.to_geojson(file_name, text="var track_ensemble_data =")

    # Loop through all models and check if they fall within cone
    models_to_add = []
    for model in cosmos.scenario.model:
        # First check if this type of model should be run in ensemble mode
        if model.type not in cosmos.scenario.ensemble_models:
            # Not an ensemble model
            continue
        if shapely.intersects(cone.loc[0]["geometry"], model.outline.loc[0]["geometry"]):
            # Add model
            # Make a shallow copy of the model
            ensemble_model = copy.copy(model)
            # Change name and long name
            ensemble_model.name = model.name + "_ensemble"
            ensemble_model.long_name = model.long_name + " (ensemble)"
            # Re-initialize the model domain
            ensemble_model.read_model_specific()
            # Set ensemble flag
            ensemble_model.ensemble = True
            # Set name of matching deterministic model
            ensemble_model.deterministic_name = model.name
            # Change nesting (new nested models will be set later in this function)
            ensemble_model.nested_flow_models = []
            ensemble_model.nested_wave_models = []
            if ensemble_model.flow_nested_name:
                ensemble_model.flow_nested_name += "_ensemble"
            if ensemble_model.wave_nested_name:
                ensemble_model.wave_nested_name += "_ensemble"
            if ensemble_model.bw_nested_name:
                ensemble_model.bw_nested_name += "_ensemble"
            # Add to list of models to add    
            models_to_add.append(ensemble_model)

    cosmos.scenario.model = cosmos.scenario.model + models_to_add

    for model in models_to_add:
        # Get nested models for ensemble models
        model.get_nested_models()
        # Set and make paths for ensemble models
        model.set_paths()
    
    if cosmos.config.run.only_run_ensemble:
        # Remove all models that are not ensembles       
        cosmos.scenario.model = [model for model in cosmos.scenario.model if model.ensemble]

    # Set ensemble names
    cosmos.scenario.ensemble_names = []
    for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
        cosmos.scenario.ensemble_names.append(str(iens).zfill(5))

    # Upload spw files to S3
    if cosmos.config.run.run_mode == "cloud":
        cosmos.log("Uploading spiderweb files to S3")
        path = cosmos.scenario.cycle_track_ensemble_spw_path
        subfolder = cosmos.scenario.name + "/track_ensemble/spw"
        cosmos.cloud.upload_folder("cosmos-scenarios", path, subfolder)

    cosmos.log("Track ensemble done ...")
  

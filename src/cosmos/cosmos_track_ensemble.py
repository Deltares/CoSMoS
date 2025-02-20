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
import geopandas as gpd

from .cosmos_main import cosmos
from cht_cyclones.tropical_cyclone import TropicalCycloneEnsemble
# from cht_meteo.cht.meteo.meteo import filter_cyclones_TCvitals, find_priorityTC
import cht_utils.fileops as fo
from datetime import datetime
import cht_utils.misc_tools

def setup_track_ensemble():

    tc = cosmos.tropical_cyclone
    
    if len(tc.track.gdf) < 3:
        # Track too short
        return

    # Check if track ensemble is already generated in a previous attempt
    if os.path.exists(cosmos.scenario.cycle_track_ensemble_path):
        # Track ensemble already generated
        ensemble_generated_before = True
    else:
        ensemble_generated_before = False

    tstart = cosmos.cycle.replace(tzinfo=None)
    tend   = cosmos.stop_time.replace(tzinfo=None)
    dt     = 3
    nens   = cosmos.scenario.track_ensemble_nr_realizations
    track_path = cosmos.scenario.cycle_track_ensemble_cyc_path
    spw_path   = cosmos.scenario.cycle_track_ensemble_spw_path    

    if not ensemble_generated_before:

        # Generate track ensemble
        cosmos.log("Generating track ensemble ...")

        cosmos.scenario.track_ensemble = tc.make_ensemble(name="ensemble",
                                                          number_of_realizations=nens,
                                                          dt=dt,
                                                          tstart=tstart,
                                                          tend=tend,
                                                          track_path=track_path,
                                                          spw_path=spw_path,
                                                          mean_abs_cte24=cosmos.config.track_ensemble.mean_abs_cte24, # mean absolute error in cross-track error (CTE) in NM
                                                          sc_cte=cosmos.config.track_ensemble.sc_cte,  # auto-regression CTE; typically >1
                                                          mean_abs_ate24=cosmos.config.track_ensemble.mean_abs_ate24, # mean absolute error in along-track error (ATE) in NM
                                                          sc_ate=cosmos.config.track_ensemble.sc_ate,  # auto-regression ATE; typically >1 
                                                          mean_abs_ve24=cosmos.config.track_ensemble.mean_abs_ve24,  # mean absolute error in wind error (VE) in knots
                                                          sc_ve=cosmos.config.track_ensemble.sc_ve,  # auto-regression VE = 1 = no auto-regression
                                                          bias_ve=cosmos.config.track_ensemble.bias_ve  # bias per hour
                                                         )


        trks = cosmos.scenario.track_ensemble.to_gdf(option="tracks",
                                                     varname="track_ensemble_data", 
                                                     filename=os.path.join(cosmos.scenario.cycle_track_ensemble_path, "track_ensemble.geojson.js"))


        trks = cosmos.scenario.track_ensemble.to_gdf(option="tracks",
                                                     filename=os.path.join(cosmos.scenario.cycle_track_ensemble_path, "track_ensemble.pli"))

        # Get outline of ensemble
        cone = cosmos.scenario.track_ensemble.to_gdf(option="outline",
                                                    buffer=200000.0,
                                                    filename=os.path.join(cosmos.scenario.cycle_track_ensemble_path, "ensemble_cone.geojson"))
 
    else:
        # Could also read in ensemble from file, but then we need to build that functionality in the TropicalCycloneEnsemble class
        cosmos.scenario.track_ensemble = TropicalCycloneEnsemble(tc,
                                                                 number_of_realizations=nens,
                                                                 dt=dt,
                                                                 tstart=tstart,
                                                                 tend=tend,
                                                                 track_path=track_path,
                                                                 spw_path=spw_path)

        # Read the cone from geojson file and turn into gdf
        cone = gpd.read_file(os.path.join(cosmos.scenario.cycle_track_ensemble_path, "ensemble_cone.geojson"))

    # Loop through all models and check if they fall within cone
    models_to_add = []
    for model in cosmos.scenario.model:
        # First check if this type of model should be run in ensemble mode
        if model.type not in cosmos.scenario.ensemble_models:
            # Not an ensemble model
            continue
        if model.outline is None:
            # No outline defined
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
    
    # if cosmos.config.run.only_run_ensemble:
    #     # Remove all models that are not ensembles       
    #     cosmos.scenario.model = [model for model in cosmos.scenario.model if model.ensemble]

    # Set ensemble names
    cosmos.scenario.ensemble_names = []
    for iens in range(cosmos.scenario.track_ensemble_nr_realizations):
        cosmos.scenario.ensemble_names.append(str(iens).zfill(5))

    cosmos.log("Track ensemble done ...")
  

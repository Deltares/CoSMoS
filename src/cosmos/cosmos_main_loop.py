# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import time
import datetime
import sched
import os
import numpy as np

from .cosmos_main import cosmos
from .cosmos_meteo import read_meteo_sources
from .cosmos_meteo import download_and_collect_meteo
from .cosmos_stations import Stations
from .cosmos_scenario import Scenario
from .cosmos_configuration import read_config_file
#from .cosmos_tiling import tile_layer

import cht.misc.fileops as fo
import cht.misc.xmlkit as xml
#from cht.tiling.tiling import TileLayer

class MainLoop:
    
    def __init__(self):
        # Try to kill all instances of main loop and model loop
        self.just_initialize = False
        self.run_models      = True
        self.clean_up        = True
    
    def start(self, cycle_time=None):
        
        # Determines cycle time and runs main loop

        cosmos.log("Starting main loop ...")
        
        # Read xml config file
        read_config_file()
        
        xml_file = os.path.join(cosmos.config.main_path,
                    "scenarios",
                    cosmos.config.scenario_name,
                    cosmos.config.scenario_name + ".xml")
        xml_obj = xml.xml2obj(xml_file)
        
        # Determine cycle time
        if not cycle_time:
            
            # Cycle time not given. This is the first time this loop is run.
            # Check if this is a forecast or hindcast.
            
            if hasattr(xml_obj, "cycle"):
                # First cycle in hindcast
                cosmos.config.forecast = False
                cosmos.cycle_time = xml_obj.cycle[0].value.replace(tzinfo=datetime.timezone.utc)
            else:
                # First cycle in forecast
                cosmos.config.forecast = True
                delay = 0
                t = datetime.datetime.now(datetime.timezone.utc) - \
                    datetime.timedelta(hours=delay)
                h0 = t.hour
                h0 = h0 - np.mod(h0, cosmos.config.cycle_interval)
                cosmos.cycle_time = t.replace(microsecond=0, second=0, minute=0, hour=h0)

            cosmos.stop_time = cosmos.cycle_time + \
                datetime.timedelta(hours=xml_obj.runtime[0].value)    
            cosmos.next_cycle_time = cosmos.cycle_time + datetime.timedelta(hours=cosmos.config.cycle_interval)
            
            # Cycle given in config, so override cycle_time
            if cosmos.config.cycle:
                cosmos.next_cycle_time = cosmos.cycle_time + datetime.timedelta(hours=cosmos.config.cycle_interval)
                cosmos.cycle_time = cosmos.config.cycle
                cosmos.stop_time = cosmos.cycle_time + \
                    datetime.timedelta(hours=xml_obj.runtime[0].value)    
                # Set back to None, so it's not used anymore in the next cycle                
                cosmos.config.cycle = None
                                
            if hasattr(xml_obj, "last_cycle"):
                cosmos.cycle_stop_time = xml_obj.last_cycle[0].value.replace(tzinfo=datetime.timezone.utc)                        
            
        else:
            # Cycle time given as input from last model loop iteration
            cosmos.cycle_time = cycle_time
            cosmos.stop_time = cosmos.cycle_time + \
                datetime.timedelta(hours=xml_obj.runtime[0].value)    
            cosmos.next_cycle_time = cosmos.cycle_time + datetime.timedelta(hours=cosmos.config.cycle_interval)
                    
        cosmos.cycle_string = cosmos.cycle_time.strftime("%Y%m%d_%Hz")


        delay = datetime.timedelta(hours=0) # Delay in hours
        
        # Check whether last cycle is currently running. If so, next_cycle_time is set to None
        if cosmos.cycle_stop_time:
            if cosmos.cycle_time>cosmos.cycle_stop_time:
                cosmos.next_cycle_time = None

        # Determine time at which this cycle should start running
        
        tnow = datetime.datetime.now(datetime.timezone.utc)
        if tnow > cosmos.cycle_time + delay:
            # start now
            start_time = tnow + datetime.timedelta(seconds=1)
        else:
            # start after delay
            start_time = cosmos.cycle_time + delay
        self.scheduler = sched.scheduler(time.time, time.sleep)
        dt = start_time - tnow
        
        cosmos.log("Next cycle " + cosmos.cycle_string + " will start at " + start_time.strftime("%Y-%m-%d %H:%M:%S") + " UTC")
        
        # Kick off main_loop run
        self.scheduler.enter(dt.seconds, 1, self.run, ())
        self.scheduler.run()

    def run(self):
        
        # Start by reading all available models, stations, etc.
        cosmos.log("Starting cycle ...")    
 
        # Read xml config file (again, but maybe something was changed while cosmos was waiting)
        cosmos.log("Reading config file ...")    
        read_config_file()
        
        # Available stations
        cosmos.log("Reading stations ...")    
        cosmos.stations = Stations()
        cosmos.stations.read()

        # Available meteo sources
        cosmos.log("Reading meteo sources ...")    
        read_meteo_sources()


        # Find all available super regions
        cosmos.log("Reading super regions ...")    
        cosmos.super_region = {}
        super_region_path = os.path.join(cosmos.config.main_path, "super_regions")
        super_region_list = fo.list_files(os.path.join(super_region_path, "*.xml"))
        for super_file in super_region_list:
            name = os.path.splitext(os.path.basename(super_file))[0]
            cosmos.super_region[name] = []
            xml_obj = xml.xml2obj(super_file)
            for region in xml_obj.region:
                cosmos.super_region[name].append(region.value.lower())
        
        # Find all available models and store in dict cosmos.all_models
        cosmos.log("Finding available models ...")    
        cosmos.all_models = {}
        region_list = fo.list_folders(os.path.join(cosmos.config.main_path,
                                                   "models", "*"))
        for region_path in region_list:
            region_name = os.path.basename(region_path)
            type_list = fo.list_folders(os.path.join(region_path,"*"))
            for type_path in type_list:
                type_name = os.path.basename(type_path)
                name_list = fo.list_folders(os.path.join(type_path,"*"))
                for name_path in name_list:
                    name = os.path.basename(name_path).lower()
                    # Check if xml file exists
                    xml_file = os.path.join(name_path, name + ".xml")
                    if os.path.exists(xml_file):
                        cosmos.all_models[name] = {"type": type_name,
                                                   "region": region_name}
                
        # Scenario
        cosmos.log("Reading scenario ...")
        cosmos.scenario = Scenario(cosmos.config.scenario_name)
        cosmos.scenario.path = os.path.join(cosmos.config.main_path,
                                          "scenarios",
                                          cosmos.config.scenario_name)
        cosmos.scenario.file_name = os.path.join(cosmos.scenario.path,
                                                 cosmos.config.scenario_name + ".xml")

        # Read scenario and add models (the models are also initialized here)
        # This is also where all the scenario and model paths are set
        cosmos.scenario.read()
        
        if self.clean_up:
            # Don't allow clean up when just initializing or continuous mode
            if not self.just_initialize and cosmos.config.cycle_mode == "single_shot":           
                # Remove old directories
                pths = fo.list_folders(os.path.join(cosmos.scenario.path,"*"))
                for pth in pths:
                    fo.rmdir(pth)
                fo.rmdir(os.path.join(cosmos.config.job_path,
                                      cosmos.config.scenario_name))

        # Remove older cycles
        if not self.just_initialize and cosmos.config.cycle_mode == "continuous":           
            if cosmos.config.remove_old_cycles>0 and not cosmos.storm_flag:
                # Get list of all cycles
                cycle_list = fo.list_folders(os.path.join(cosmos.scenario.path,"*z"))

                tkeep = cosmos.cycle_time.replace(tzinfo=None) - datetime.timedelta(hours=cosmos.config.remove_old_cycles)
                for cycle in cycle_list:
                    if cycle in cosmos.storm_keeplist:
                        continue
                    t = datetime.datetime.strptime(cycle[-12:],"%Y%m%d_%Hz")
                    if t<tkeep:
                        cosmos.log("Removing older cycle : " + cycle[-12:])
                        fo.rmdir(cycle)
            elif cosmos.storm_flag:
                cycle_list = fo.list_folders(os.path.join(cosmos.scenario.path,"*z"))
                cosmos.storm_keeplist.append(cycle_list[-1])
                        
        # Create scenario cycle paths
        fo.mkdir(cosmos.scenario.cycle_path)
        fo.mkdir(cosmos.scenario.cycle_models_path)
        fo.mkdir(cosmos.scenario.cycle_tiles_path)
        fo.mkdir(cosmos.scenario.cycle_job_list_path)

        # Prepare models and determine which models are nested in which
        cosmos.log("Preparing models ...")
        for model in cosmos.scenario.model:

            model.prepare()
            
            if model.flow_nested_name:
                # Look up model from which it gets it boundary conditions
                for model2 in cosmos.scenario.model:
                    if model2.name == model.flow_nested_name:
                        model.flow_nested = model2
                        model2.nested_flow_models.append(model)
                        break
            if model.wave_nested_name:
                # Look up model from which it gets it boundary conditions
                for model2 in cosmos.scenario.model:
                    if model2.name == model.wave_nested_name:
                        model.wave_nested = model2
                        model2.nested_wave_models.append(model)
                        break

        # Get list of models that have already finished
        finished_list = os.listdir(cosmos.scenario.cycle_job_list_path)

        # Set initial durations and what needs to be done for each model
        for model in cosmos.scenario.model:

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
                
            # Find matching meteo subset
            if model.meteo_dataset:
               for subset in cosmos.meteo_subset:
                   if subset.name == model.meteo_dataset:
                       model.meteo_subset = subset
                       break

        # Start and stop times
        cosmos.log('Getting start and stop times ...')
        # In case of a forecast ...
        get_start_and_stop_times()
        
        # Set reference date to minimum of all start times
        rfdate = datetime.datetime(2200, 1, 1, 0, 0, 0)
        for model in cosmos.scenario.model:
            if model.flow:
                rfdate = min(rfdate, model.flow_start_time)
            if model.wave:
                rfdate = min(rfdate, model.wave_start_time)                
        cosmos.scenario.ref_date = datetime.datetime(rfdate.year,
                                                     rfdate.month,
                                                     rfdate.day,
                                                     0, 0, 0)
        
        # Write start and stop times to log file
        for model in cosmos.scenario.model:
            if model.flow:
                cosmos.log(model.long_name + " : " + \
                           model.flow_start_time.strftime("%Y%m%d %H%M%S") + " - " + \
                           model.flow_stop_time.strftime("%Y%m%d %H%M%S"))
            else:    
                cosmos.log(model.long_name + " : " + \
                           model.wave_start_time.strftime("%Y%m%d %H%M%S") + " - " + \
                           model.wave_stop_time.strftime("%Y%m%d %H%M%S"))

        # # Initialize tile layers
        # tile_layer              = {}
        # tile_layer["flood_map"] = TileLayer("flood_map")

        if not self.just_initialize:
            
            # Get meteo data
            download_and_collect_meteo()
            
            if self.run_models:        
                # And now start the model loop
                cosmos.log("Starting model loop ...")
                cosmos.model_loop.start()

def get_start_and_stop_times():
        
    y = cosmos.cycle_time.year
    cosmos.reference_time = datetime.datetime(y, 1, 1)
    
    start_time  = cosmos.cycle_time
        
    stop_time = cosmos.stop_time    
        
    start_time = start_time.replace(tzinfo=None)    
    stop_time  = stop_time.replace(tzinfo=None)    
    
    cosmos.stop_time = stop_time

    # Find all the models that do not have any models nested in them

    # First waves

    for model in cosmos.scenario.model:        
        if model.wave:
            model.wave_start_time = start_time
            model.wave_stop_time  = stop_time
    
    not_nested_models = []
    for model in cosmos.scenario.model:
        if model.wave:
            # This is a wave model
            if not model.nested_wave_models:
                # And it does not have any model nested in it
                not_nested_models.append(model)

    # Now for each of these models, loop up in the model tree until
    # not nested in any other model            
    for not_nested_model in not_nested_models:
        
        nested = True        
        model = not_nested_model
        nested_wave_start_time = start_time
        
        while nested:
            
            model.wave_start_time = min(model.wave_start_time,
                                        nested_wave_start_time)
            
            # Check for restart files
            restart_time, restart_file = check_for_wave_restart_files(model)
            if not restart_time:
                # No restart file available, so subtract spin-up time
                tok = start_time - datetime.timedelta(hours=model.wave_spinup_time)
                model.wave_start_time = min(model.wave_start_time, tok)
                model.wave_restart_file = None
            else:    
                model.wave_start_time   = restart_time
                model.wave_restart_file = restart_file
                        
            if model.wave_nested:                
                # This model gets it's wave boundary conditions from another model                
                nested_wave_start_time = model.wave_start_time
                model = model.wave_nested
                
            else:
                # Done looping through the tree
                nested = False

    # And now flow
    
    for model in cosmos.scenario.model:
        if model.flow:
            if model.wave:
                model.flow_start_time = model.wave_start_time
                model.flow_stop_time  = model.wave_stop_time
            else:
                model.flow_start_time = start_time
                model.flow_stop_time  = stop_time
    
    not_nested_models = []
    for model in cosmos.scenario.model:
        if model.flow:
            # This is a flow model
            if not model.nested_flow_models:
                # And it does not have any model nested in it
                not_nested_models.append(model)

    # Now for each of these models, loop up in the model tree until
    # not nested in any other model            
    for not_nested_model in not_nested_models:
        
        nested = True        
        model = not_nested_model
        nested_flow_start_time = start_time
        
        while nested:
            
            model.flow_start_time = min(model.flow_start_time,
                                        nested_flow_start_time)
            
            # Check for restart files
            restart_time, restart_file = check_for_flow_restart_files(model)

            if not restart_time:
                # No restart file available, so subtract spin-up time
                tok = start_time - datetime.timedelta(hours=model.flow_spinup_time)
                model.flow_start_time = min(model.flow_start_time, tok)
                model.flow_restart_file = None
            else:    
                model.flow_start_time   = restart_time
                model.flow_restart_file = restart_file
                        
            if model.flow_nested:                
                # This model gets it's flow boundary conditions from another model                
                nested_flow_start_time = model.flow_start_time
                # On to the next model in the chain
                model = model.flow_nested
                
            else:
                # Done looping through the tree
                nested = False

    # For only wave model, also add flow start and stop time (used for meteo)
    for model in cosmos.scenario.model:        
        if model.wave:
            if not model.flow_start_time:
                model.flow_start_time = model.wave_start_time
            if not model.flow_stop_time:
                model.flow_stop_time = model.wave_stop_time

def check_for_wave_restart_files(model):
    
    restart_time = None
    restart_file = None
    
    path = model.restart_wave_path

    if os.path.exists(path): 
        restart_list = os.listdir(path)
        times = []
        files = []
        for file_name in restart_list:
            tstr = file_name[-19:-4]
            t    = datetime.datetime.strptime(tstr,
                                              '%Y%m%d.%H%M%S')
            times.append(t)
            files.append(file_name)
        
        # Now find the last time that is greater than the start time
        # and smaller than 
        for it, t in enumerate(times):
            if t>model.wave_start_time - datetime.timedelta(hours=model.wave_spinup_time) and t<=model.wave_start_time:
                restart_time = t
                restart_file = files[it]
    else:
        fo.mkdir(path)
    
    return restart_time, restart_file

def check_for_flow_restart_files(model):
    
    restart_time = None
    restart_file = None
    
    path = model.restart_flow_path

    if os.path.exists(path): 
        restart_list = os.listdir(path)
        times = []
        files = []
        for file_name in restart_list:
            tstr = file_name[-19:-4]
            t    = datetime.datetime.strptime(tstr,
                                              '%Y%m%d.%H%M%S')
            times.append(t)
            files.append(file_name)
        
        # Now find the last time that is greater than the start time
        # and smaller than 
        for it, t in enumerate(times):
            if t>=model.flow_start_time - datetime.timedelta(hours=model.flow_spinup_time) and t<=model.flow_start_time:
                restart_time = t
                restart_file = files[it]
    else:
        fo.mkdir(path)
                
    return restart_time, restart_file


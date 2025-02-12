# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:29:26 2021

@author: ormondt
"""
import os
import toml

from .cosmos_main import cosmos
from .cosmos_cluster import cluster_dict
from .cosmos_cluster import Cluster

class Scenario:
    """Scenario class to read scenario file and initialize models. 

    See Also
    ----------
    cosmos.cosmos_main_loop.MainLoop
    cosmos.cosmos_model_loop.ModelLoop
    cosmos.cosmos_model.Model

    """  
    def __init__(self, name):
        """Initialize cosmos scenario.

        Parameters
        ----------
        name : str
            Name of scenario to be executed.
        """        

        self.name          = name
        self.model         = []
        self.long_name     = name
        self.description   = name
        self.cycle         = None
        self.lon           = cosmos.config.webviewer.lon
        self.lat           = cosmos.config.webviewer.lat
        self.zoom          = cosmos.config.webviewer.zoom
        self.path          = None
        self.cycle_path    = None
        self.tile_path     = None
        self.job_list_path = None
        self.restart_path  = None
        self.last_cycle    = None 
        self.cyclone_track              = None 
        self.tropical_cyclone           = None 
        self.track_ensemble             = None 
        self.track_ensemble_nr_realizations = cosmos.config.track_ensemble.nr_realizations
        self.ensemble_models            = cosmos.config.run.ensemble_models
        self.meteo_dataset              = None
        self.meteo_spiderweb            = None
        self.meteo_wind                 = True
        self.meteo_atmospheric_pressure = True
        self.meteo_precipitation        = True
        self.meteo_track                = None
        self.observations_path = ""
        self.run_ensemble = False
        self.meteo_string = ""
        self.storm_number = None
        
    def read(self):
        """Read scenario file, set model paths and settings, initialize models and read model generic and model specific data. 
        """

        # Read scenario file
        cosmos.log("Reading scenario file ...")        
        self.path = os.path.join(cosmos.config.path.scenarios, self.name)
        scenario_file = os.path.join(self.path, "scenario.toml")     
        sc_dict = toml.load(scenario_file)

        # Turn into object        
        for key, value in sc_dict.items():
            if key == "model" or key == "cluster":
                pass
            else:    
                setattr(self, key, value)        

                
            

        # First find all the models and store in dict models_in_scenario
        models_in_scenario = {}
        for mdl in sc_dict["model"]:                        
            # Add the models in this scenario                     
            if "name" in mdl:
                # Individual model
                name = mdl["name"].lower()
                models_in_scenario[name] = cosmos.all_models[name]
                # Set meteo to one give in scenario
                models_in_scenario[name]["meteo_dataset"] = self.meteo_dataset
                models_in_scenario[name]["meteo_spiderweb"] = self.meteo_spiderweb
                models_in_scenario[name]["meteo_track"] = self.meteo_track
                # But override is separate dataset is provided for model
                if "meteo_dataset" in mdl:
                    models_in_scenario[name]["meteo_dataset"] = mdl["meteo_dataset"]
                if "meteo_spiderweb" in mdl:
                    models_in_scenario[name]["meteo_spiderweb"] = mdl["meteo_spiderweb"]
                if "meteo_track" in mdl:
                    models_in_scenario[name]["meteo_track"] = mdl["meteo_track"]
                                                        
            else:
                
                # Model by region and type                
                # First make list of all regions to include
                region_list       = ["empty"] # List of regions
                type_list         = ["empty"] # List of types

                if "type" in mdl:
                    type_list = mdl["type"]
                if "region" in mdl:
                    region_list.append(mdl["region"])
                if "super_region" in mdl:
                    super_region_name = mdl["super_region"].lower()
                    for region in cosmos.config.super_region[super_region_name]["region"]:
                        if not region in region_list:
                            region_list.append(region)

                # Loop through all available models
                for name in cosmos.all_models.keys():
                    if any(cosmos.all_models[name]["region"] == item for item in region_list):
                        if cosmos.all_models[name]["type"] in type_list:
                            models_in_scenario[name] = cosmos.all_models[name]
                            # Set meteo to one give in scenario
                            models_in_scenario[name]["meteo_dataset"] = self.meteo_dataset
                            models_in_scenario[name]["meteo_spiderweb"] = self.meteo_spiderweb
                            models_in_scenario[name]["meteo_track"] = self.meteo_track
                            # But override is separate dataset is provided for model
                            if "meteo_dataset" in mdl:
                                models_in_scenario[name]["meteo_dataset"] = mdl["meteo_dataset"]
                            if "meteo_spiderweb" in mdl:
                                models_in_scenario[name]["meteo_spiderweb"] = mdl["meteo_spiderweb"]
                            if "meteo_track" in mdl:
                                models_in_scenario[name]["meteo_track"] = mdl["meteo_track"]

        ### Add missing models
        # We know which models need to be added. Check if all models that provide boundary conditions are there as well.
        # TO DO: the above ...                        
                                
                        
        ### Clear model list
        self.model = []

        # Loop through models in scenario         
        for name in models_in_scenario.keys():
            
            tp     = models_in_scenario[name]["type"]
            
            # Initialize models
            if tp.lower() == "ww3":
                from cosmos.cosmos_ww3 import CoSMoS_WW3
                model = CoSMoS_WW3()
                model.wave = True
            elif tp.lower() == "hurrywave":
                from cosmos.cosmos_hurrywave import CoSMoS_HurryWave
                model = CoSMoS_HurryWave()
                model.wave = True
            elif tp.lower() == "sfincs":
                from cosmos.cosmos_sfincs import CoSMoS_SFINCS
                model = CoSMoS_SFINCS()
                model.flow = True
            elif tp.lower() == "delft3dfm":
                from cosmos.cosmos_delft3dfm import CoSMoS_Delft3DFM
                model = CoSMoS_Delft3DFM()
                model.flow = True
            elif tp.lower() == "xbeach":
                from cosmos.cosmos_xbeach import CoSMoS_XBeach
                model = CoSMoS_XBeach()
                model.wave = True
                model.flow = True
            elif tp.lower() == "beware":
                from cosmos.cosmos_beware import CoSMoS_BEWARE
                model = CoSMoS_BEWARE()
                model.wave = True
                model.flow = True

            # Set model paths
            # Path where model sits in model database                        
            region = models_in_scenario[name]["region"]
            vsn    = "001"

            model_path = os.path.join(cosmos.config.model_database.path,
                                      region, tp, name)
            file_name = os.path.join(model_path, "model.toml")

            # Path in model database
            model.path        = model_path
            model.name        = name
            model.deterministic_name = name
            model.version     = vsn
            model.region      = region
            model.file_name   = file_name
            model.type        = tp

            model.meteo_dataset              = models_in_scenario[name]["meteo_dataset"]
            model.meteo_spiderweb            = models_in_scenario[name]["meteo_spiderweb"]
            model.meteo_track                = models_in_scenario[name]["meteo_track"]

            # If wind/pressure/rain are actively turned off in scenario, also do it here    
            if not self.meteo_wind and model.meteo_wind:
                model.meteo_wind = False
            if not self.meteo_atmospheric_pressure and model.meteo_atmospheric_pressure:
                model.meteo_atmospheric_pressure = False
            if not self.meteo_precipitation and model.meteo_precipitation:
                model.meteo_precipitation = False
            if not self.meteo_dataset and not model.meteo_dataset:
                model.meteo_wind = False
                model.meteo_atmospheric_pressure = False
                model.meteo_precipitation = False

            model.flow_start_time            = None
            model.flow_stop_time             = None

            model.tide = True

            # Read in model generic data (from toml file)
            model.read_generic()

            # Read in model specific data (input files)
            # Should move this bit to pre-processing of model
            model.read_model_specific()
            
            # Find matching meteo dataset
            if model.meteo_dataset:
               # Loop through all available meteo datasets
               for dataset_name, meteo_dataset in cosmos.meteo_database.dataset.items():
                   if dataset_name == model.meteo_dataset:
                       model.meteo_dataset = meteo_dataset
                       break

            # Get stations to add from scenario
            if "station" in sc_dict:
                for station in sc_dict["station"]:
                    toml_file_name = station["name"] # toml file name
                    if "model_type" in station:
                        mdltype = station["model_type"]
                        if tp.lower() in mdltype:
                            model.add_stations(toml_file_name)
                    if "model_name" in station:
                        mdlname = station["model_name"]
                        if name.lower() in mdlname:
                            model.add_stations(toml_file_name)

            self.model.append(model)

        # Add models to clusters 
        if "cluster" in sc_dict:
            for cld in sc_dict["cluster"]:
                cl = Cluster(name = cld['name'])
                if "run_condition" in cld:
                    cl.run_condition = cld["run_condition"]
                if "topn" in cld:
                    cl.topn = cld["topn"]
                if "hm0fac" in cld:
                    cl.hm0fac = cld["hm0fac"]
                if "boundary_twl_margin" in cld:
                    cl.boundary_twl_margin = cld["boundary_twl_margin"]
                if "use_threshold" in cld:
                    if cld["use_threshold"] == "y":
                        cl.use_threshold = True
                    else:
                        cl.use_threshold = False
                if cl.run_condition == "topn":
                    cl.ready = False
                # Add models to this cluster    
                region_list       = [] # List of regions
                type_list         = [] # List of types
                if "region" in cld:
                    for region in cld["region"]:
                        if not region in region_list:
                            region_list.append(region)
                if "type" in cld:
                    for tp in cld["type"]:
                        type_list.append(tp)
                if "super_region" in cld:
                    super_region_name = cld["super_region"].lower()
                    for region in cosmos.config.super_region[super_region_name]["region"]:
                        if not region in region_list:
                            region_list.append(region)

                # Loop through all available models
                for model in self.model:
                    okay = True
                    if type_list:
                        if not model.type in type_list:
                            okay = False
                            continue
                    if not model.flow_nested_name and not model.wave_nested_name:
                        okay = False
                        continue                                            
                    # Filter by region
                    if region_list:
                        if not model.region in region_list:
                            # Region of this model is not in region_list
                            okay = False
                            continue
                    # Filter by type
                    if okay:
                        cl.add_model(model)
                    
                cluster_dict[cld['name']] = cl                   

        cosmos.log("Finished reading scenario")    

    def set_paths(self):
        """Set cycle paths.
        """   
        self.cycle_path            = os.path.join(self.path, cosmos.cycle_string)
        self.cycle_models_path     = os.path.join(self.path, cosmos.cycle_string, "models")
        self.cycle_tiles_path      = os.path.join(self.path, cosmos.cycle_string, "tiles")
        self.cycle_job_list_path   = os.path.join(self.path, cosmos.cycle_string, "job_list")
        self.cycle_track_ensemble_path    = os.path.join(self.path, cosmos.cycle_string, "track_ensemble")
        self.cycle_track_ensemble_cyc_path    = os.path.join(self.path, cosmos.cycle_string, "track_ensemble", "cyc")
        self.cycle_track_ensemble_spw_path    = os.path.join(self.path, cosmos.cycle_string, "track_ensemble", "spw")
        self.cycle_track_spw_path    = os.path.join(self.path, cosmos.cycle_string, "track")
        self.restart_path          = os.path.join(self.path, "restart")
        self.timeseries_path       = os.path.join(self.path, "timeseries")
        self.cycle_timeseries_path = os.path.join(self.path, "timeseries", cosmos.cycle_string)

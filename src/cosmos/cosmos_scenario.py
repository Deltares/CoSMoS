# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:29:26 2021

@author: ormondt
"""
import os
import toml

from .cosmos import cosmos
from .cosmos_cluster import cluster_dict
from .cosmos_cluster import Cluster

# from cht.misc import fileops as fo
# from cht.misc import xmlkit as xml

class Scenario:
    
    def __init__(self, name):

        self.name          = name
        self.model         = []
        self.long_name     = name
        self.description   = name
        self.lon           = 0.0
        self.lat           = 0.0
        self.zoom          = 10
        self.path          = None
        self.cycle_path    = None
        self.tile_path     = None
        self.job_list_path = None
        self.restart_path  = None
        self.last_cycle    = None 
        self.track_ensemble             = None 
        self.track_ensemble_nr_realizations = 0 
        self.meteo_dataset              = None
        self.meteo_spiderweb            = None
        self.meteo_wind                 = True
        self.meteo_atmospheric_pressure = True
        self.meteo_precipitation        = True
        self.meteo_track                = None
        self.observations_path = ""
        
    def read(self):
        
        # Read scenario file
        cosmos.log("Reading scenario file ...")        
        self.path = os.path.join(cosmos.config.path.scenarios, self.name)
        scenario_file = os.path.join(self.path, "scenario.toml")     
        sc_dict = toml.load(scenario_file)

        # Turn into object        
        for key, value in sc_dict.items():
            if key == "model":
                pass
            else:    
#                for key, value in sc_dict[key].items():
                setattr(self, key, value)
        
        # ### Ensemble

        # if hasattr(xml_obj, "track_ensemble"):
        #     self.track_ensemble = xml_obj.track_ensemble[0].value
        #     cosmos.scenario.member_names = []
        #     ensemble_path = os.path.join(cosmos.config.main_path,
        #                                  "meteo",
        #                                  self.track_ensemble)
        #     file_names = fo.list_files(os.path.join(ensemble_path, "*.spw"))
        #     # Loop through file names
        #     for file_name in file_names:                
        #         if file_name[-13:-4]=="besttrack":
        #             cosmos.scenario.best_track_file = os.path.join(ensemble_path,
        #                                                            file_name)
        #         else:
        #             cosmos.scenario.member_names.append(os.path.split(file_name)[1][0:-4])
            
        # else:
        #     self.track_ensemble = None
            
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
                # But override is separate dataset is provided for model
                if "meteo_dataset" in mdl:
                    models_in_scenario[name]["meteo_dataset"] = mdl["meteo_dataset"]
                if "meteo_spiderweb" in mdl:
                    models_in_scenario[name]["meteo_spiderweb"] = mdl["meteo_spiderweb"]
                                                        
            else:
                
                # Model by region and type                
                # First make list of all regions to include
                region_list       = [] # List of regions
                type_list         = [] # List of types

                if "type" in mdl:
                    type_list = mdl["type"]
                if "region" in mdl:
                    region_list = mdl["region"]
                if "super_region" in mdl:
                    for spr in mdl["super_region"]:
                        super_region_name = spr.lower()
                        for region in cosmos.config.super_region[super_region_name]["region"]:
                            if not region in region_list:
                                region_list.append(region)

                # Loop through all available models
                for name in cosmos.all_models.keys():
                    if cosmos.all_models[name]["region"] in region_list:
                        if cosmos.all_models[name]["type"] in type_list:
                            models_in_scenario[name] = cosmos.all_models[name]
                            # Set meteo to one give in scenario
                            models_in_scenario[name]["meteo_dataset"] = self.meteo_dataset
                            models_in_scenario[name]["meteo_spiderweb"] = self.meteo_spiderweb
                            # But override is separate dataset is provided for model
                            if "meteo_dataset" in mdl:
                                models_in_scenario[name]["meteo_dataset"] = mdl["meteo_dataset"]
                            if "meteo_spiderweb" in mdl:
                                models_in_scenario[name]["meteo_spiderweb"] = mdl["meteo_spiderweb"]

        ### Add missing models
        # We know which models need to be added. Check if all models that provide boundary conditions are there as well.
                        
        ### Clear model list
        self.model = []

        # Loop through models in scenario         
        for name in models_in_scenario.keys():
            
            print(name)            
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
            model.version     = vsn
            model.region      = region
            model.file_name   = file_name
            model.type        = tp

            model.meteo_dataset              = models_in_scenario[name]["meteo_dataset"]
            model.meteo_spiderweb            = models_in_scenario[name]["meteo_spiderweb"]
            
            # If wind/pressure/rain are actively turned off in scenario, also do it here    
            if not self.meteo_wind and model.meteo_wind:
                model.meteo_wind = False
            if not self.meteo_atmospheric_pressure and model.meteo_atmospheric_pressure:
                model.meteo_atmospheric_pressure = False
            if not self.meteo_precipitation and model.meteo_precipitation:
                model.meteo_precipitation = False

            model.flow_start_time            = None
            model.flow_stop_time             = None

            model.tide = True

            # Read in model generic data (from xml file)
            model.read_generic()

            # # Read in model specific data (input files)
            # # Should move this bit to pre-processing of model
            model.read_model_specific()
            
            # Find matching meteo subset
            if model.meteo_dataset:
               for subset in cosmos.meteo_subset:
                   if subset.name == model.meteo_dataset:
                       model.meteo_subset = subset
                       break
                        
            self.model.append(model)
        
        # ### Add models to clusters 
        # if hasattr(xml_obj, "cluster"):
        #     for xml_cluster in xml_obj.cluster:
        #         name = xml_cluster.name[0].value.lower()
        #         cl = Cluster(name)
        #         if hasattr(xml_cluster, "run_condition"):
        #             cl.run_condition = xml_cluster.run_condition[0].value
        #         if hasattr(xml_cluster, "topn"):
        #             cl.topn = int(xml_cluster.topn[0].value)
        #         if hasattr(xml_cluster, "hm0fac"):
        #             cl.hm0fac = float(xml_cluster.hm0fac[0].value)
        #         if hasattr(xml_cluster, "boundary_twl_margin"):
        #             cl.boundary_twl_margin = float(xml_cluster.boundary_twl_margin[0].value)
        #         if hasattr(xml_cluster, "use_threshold"):
        #             if xml_cluster.use_threshold[0].value == "y":
        #                 cl.use_threshold = True
        #             else:    
        #                 cl.use_threshold = False                        
        #         if cl.run_condition == "topn":
        #             cl.ready = False
                    
        #         # Add models to this cluster    
        #         region_list       = [] # List of regions
        #         type_list         = [] # List of types

        #         if hasattr(xml_cluster, "region"):
        #             for xml_region in xml_cluster.region:
        #                 if not xml_region.value.lower() in region_list:
        #                     region_list.append(xml_region.value.lower())
        #         if hasattr(xml_cluster, "type"):
        #             for xml_type in xml_cluster.type:                    
        #                 type_list.append(xml_type.value.lower())
        #         if hasattr(xml_cluster, "super_region"):
        #             for spr in xml_cluster.super_region:
        #                 super_region_name = spr.value.lower()
        #                 for region in cosmos.super_region[super_region_name]:
        #                     if not region in region_list:
        #                         region_list.append(region)

        #         # Loop through all available models
        #         for model in self.model:
        #             okay = True
        #             if type_list:
        #                 if not model.type in type_list:
        #                     okay = False
        #                     continue
        #             if not model.flow_nested_name and not model.wave_nested_name:
        #                 okay = False
        #                 continue                                            
        #             # Filter by region
        #             if region_list:
        #                 if not model.region in region_list:
        #                     # Region of this model is not in region_list
        #                     okay = False
        #                     continue
        #             # Filter by type
        #             if okay:
        #                 cl.add_model(model)
                    
        #         cluster_dict[name] = cl                
         
        
        
        cosmos.log("Finished reading scenario")    

    def set_paths(self):
        self.cycle_path            = os.path.join(self.path, cosmos.cycle_string)
        self.cycle_models_path     = os.path.join(self.path, cosmos.cycle_string, "models")
        self.cycle_tiles_path      = os.path.join(self.path, cosmos.cycle_string, "tiles")
        self.cycle_job_list_path   = os.path.join(self.path, cosmos.cycle_string, "job_list")
        self.restart_path          = os.path.join(self.path, "restart")
        self.timeseries_path       = os.path.join(self.path, "timeseries")
        self.cycle_timeseries_path = os.path.join(self.path, "timeseries", cosmos.cycle_string)

# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
import toml

from .cosmos_stations import Stations
from .cosmos_meteo import read_meteo_sources
from .cosmos_color_maps import read_color_maps
#import cht.misc.xmlkit as xml
from cht.misc.misc_tools import rgb2hex
import cht.misc.fileops as fo

class Path:
    def __init__(self):
        self.main = None
    
class ModelDatabase:
    def __init__(self):
        self.path = None

class MeteoDatabase:
    def __init__(self):
        self.path = None

class Conda:
    def __init__(self):
        self.path = None

class Executables:
    def __init__(self):
        self.sfincs_path    = None
        self.hurrywave_path = None
        self.delft3d_path   = None
        self.xbeach_path    = None
        self.beware_path    = None

class WebServer:
    def __init__(self):
        self.hostname = None
        self.path     = None
        self.username = None
        self.password = None

class WebViewer:
    def __init__(self):
        self.name    = None
        self.version = None
        self.path    = None
        self.tile_layer = {}
        self.tile_layer["flood_map"] = {}
        self.tile_layer["flood_map"]["interval"] = 24
        self.tile_layer["flood_map"]["color_map"] = "flood_map"
        self.tile_layer["hm0"] = {}
        self.tile_layer["hm0"]["interval"] = 24
        self.tile_layer["hm0"]["color_map"] = "hm0"
        self.tile_layer["sedero"] = {}
        self.tile_layer["sedero"]["color_map"] = "sedero"
        self.tile_layer["bed_level_pre"] = {}
        self.tile_layer["bed_level_pre"]["color_map"] = "bed_level"
        self.tile_layer["bed_level_post"] = {}
        self.tile_layer["bed_level_post"]["color_map"] = "bed_level"

class CloudConfig:
    def __init__(self):
        # The url through which the Argo client is available to submit a workflow
        self.host       = None
        # Access key and secret (sort of like username/password) for reading/writing files to s3
        self.access_key = None
        self.secret_key = None
        # Region in which the Kubernetes cluster is hosted (TODO: make this configurable)
        self.region     = "eu-west-1"
        # Namespace within the cluster where the argo installation is located
        self.namespace  = "argo"
        
class Cycle:
    def __init__(self):
        self.mode            = "single_shot"
        self.interval        = 6
        self.clean_up        = False
        self.make_flood_maps = True
        self.make_wave_maps  = True
        self.upload          = True
        self.get_meteo       = True
        self.run_mode        = "serial"
        self.only_run_ensemble = False
        self.just_initialize = False
        self.run_models = True
        
class Configuration:
    """CoSMoS Configuration class.

    Set configuration for:

    - Main CoSMoS path.
    - Model database path.
    - Model executable paths.
    - Webserver and webviewer settings.
    - Cycle settings (can be overwritten by CoSMoS initialization settings).
    """   
    def __init__(self):
        self.path           = Path()
        self.model_database = ModelDatabase()
        self.meteo_database = MeteoDatabase()
        self.conda          = Conda()
        self.executables    = Executables()
        self.webserver      = WebServer()
        self.webviewer      = WebViewer()
        self.cycle          = Cycle()
        self.cloud_config   = CloudConfig()
        self.kwargs         = {}
    
    def set(self, **kwargs):
        """Set CoSMoS configuration settings.
        
        - Set configuration paths.
        - Read configuration file.
        - Overwrite values in configuration file with input arguments.
        - Find all available models in model database.
        - Read all available Stations.
        - Read all available meteo datasets.
        - Read all available super regions.
        """        

        from .cosmos_main import cosmos
                
        if kwargs:
            self.kwargs = kwargs

        self.path.config    = os.path.join(self.path.main, "configuration")     
        self.path.jobs      = os.path.join(self.path.main, "jobs")
        self.path.stations  = os.path.join(self.path.config, "stations")
        self.path.scenarios = os.path.join(self.path.main, "scenarios")
        self.path.webviewer = os.path.join(self.path.main, "webviewers")
        
        # Read config file
        self.read_config_file()

        # Now loop through kwargs to override values in config file        
        # Note: only the cycle object in config will be updated!
        for key, value in self.kwargs.items():
            setattr(self.cycle, key, value)
            
        # Now read other config data
        # Find all available models and store in dict cosmos.all_models
        cosmos.log("Finding available models ...")    
        cosmos.all_models = {}
        region_list = fo.list_folders(os.path.join(cosmos.config.model_database.path, "*"))
        for region_path in region_list:
            region_name = os.path.basename(region_path)
            type_list = fo.list_folders(os.path.join(region_path,"*"))
            for type_path in type_list:
                type_name = os.path.basename(type_path)
                name_list = fo.list_folders(os.path.join(type_path,"*"))
                for name_path in name_list:
                    name = os.path.basename(name_path).lower()
                    # Check if xml file exists
                    toml_file = os.path.join(name_path, "model.toml")
                    if os.path.exists(toml_file):
                        cosmos.all_models[name] = {"type": type_name,
                                                   "region": region_name}

        
        # Color maps
        tml_file = os.path.join(self.path.config,
                                "color_maps",
                                "map_contours.yml")
        self.map_contours = read_color_maps(tml_file)
        
        # Available stations
        cosmos.log("Reading stations ...")    
        self.stations = Stations()
        self.stations.read()

        # Available meteo sources
        cosmos.log("Reading meteo sources ...")    
        read_meteo_sources()

        # Find all available super regions
        cosmos.log("Reading super regions ...")    
        self.super_region = {}
        super_region_path = os.path.join(self.path.main, "configuration", "super_regions")
        super_region_list = fo.list_files(os.path.join(super_region_path, "*.toml"))
        for super_file in super_region_list:
            name = os.path.splitext(os.path.basename(super_file))[0]
            self.super_region[name] = toml.load(super_file)
 
        # Set webviewer path
        self.webviewer.path      = os.path.join(cosmos.config.path.main, "webviewers", self.webviewer.name)
        self.webviewer.data_path = os.path.join(cosmos.config.path.main, "webviewers", self.webviewer.name, "data")

    def read_config_file(self):
        """Read configuration file (.toml file).
        """        
        config_file = os.path.join(self.path.config,
                                   self.file_name)     

        # Read config file        
        config_dict = toml.load(config_file)
        
        # Turn into object        
        for key in config_dict:
            obj = getattr(self, key)
            for key, value in config_dict[key].items():
                setattr(obj, key, value)

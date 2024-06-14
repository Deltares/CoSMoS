# -*- coding: utf-8 -*-
"""
Created on Tue May 18 12:00:56 2021

@author: ormondt
"""

import os
import toml
from cht.misc import fileops as fo

class Station():
    """Initialize single observation station.
    """    
    def __init__(self):
        
        self.name      = None
        self.coops_id  = None 
        self.ndbc_id   = None 
        self.id        = None 
        self.long_name = None
        self.longitude = None
        self.latitude  = None
        self.type      = None
        self.mllw      = None
        self.water_level_correction = 0.0
        self.file_name = None
        self.upload    = True

class Stations():
    """Cosmos observation stations.
    """
    def __init__(self):

        self.station = []                 

    def read(self):
        """Read cosmos observation stations from observation station xml file.
        """
        from .cosmos_main import cosmos

        file_list = fo.list_files(os.path.join(cosmos.config.path.stations,
                                               "*.toml"))
        
        for file_name in file_list:

            toml_dict = toml.load(file_name)

            for toml_stat in toml_dict['station']:

                station = Station()      
                station.name      = toml_stat['name']
                station.long_name = toml_stat['longname']
                station.longitude = toml_stat['longitude']
                station.latitude  = toml_stat['latitude']
                station.type      = toml_stat['type']
                if "water_level_correction" in toml_stat:
                    station.water_level_correction = toml_stat['water_level_correction']
                if "MLLW" in toml_stat:
                    station.mllw = toml_stat['MLLW']
                if "coops_id" in toml_stat:
                    station.coops_id = toml_stat['coops_id']
                    station.id       = toml_stat['coops_id']
                if "ndbc_id" in toml_stat:
                    station.ndbc_id = toml_stat['ndbc_id']
                    station.id      = toml_stat['ndbc_id']
                if "id" in toml_stat:
                    station.id = toml_stat['id']
                    
                station.file_name = os.path.basename(file_name)    

                self.station.append(station) 

    def find_by_name(self, name):      
        """Find station name in station list.
        """
        for station in self.station:
            if station.name.lower() == name:
                return station
    
        return None

    def find_by_file(self, name):
        """Find station filename.
        """

        station_list = []
        
        for station in self.station:
            if station.file_name.lower() == name:
                station_list.append(station)

        return station_list
    
# def set_stations_to_upload():

#     for model in cosmos.scenario.model:
        
#         all_nested_models = model.get_all_nested_models(model,
#                                                   "flow",
#                                                   all_nested_models=[])
#         if all_nested_models:
#             all_nested_stations = []
#             for mdl in all_nested_models:
#                 for st in mdl.station:
#                     all_nested_stations.append(st.name)
#             for station in model.station:
#                 if station.type == "tide_gauge":
#                     if station.name in all_nested_stations:
#                         station.upload = False 

#         all_nested_models = model.get_all_nested_models(model,
#                                                   "wave",
#                                                   all_nested_models=[])
#         if all_nested_models:
#             all_nested_stations = []
#             for mdl in all_nested_models:
#                 for st in mdl.station:
#                     all_nested_stations.append(st.name)
#             for station in model.station:
#                 if station.type == "wave_buoy":
#                     if station.name in all_nested_stations:
#                         station.upload = False 

# def get_all_nested_models(model, tp, all_nested_models=[]):
    
#     if tp == "flow":
#         for mdl in model.nested_flow_models:
#             all_nested_models.append(mdl)
#             if mdl.nested_flow_models:
#                 all_nested_models = get_all_nested_models(mdl,
#                                     "flow",
#                                     all_nested_models=all_nested_models)
    
#     if tp == "wave":
#         for mdl in model.nested_wave_models:
#             all_nested_models.append(mdl)
#             if mdl.nested_wave_models:
#                 all_nested_models = get_all_nested_models(mdl,
#                                     "wave",
#                                     all_nested_models=all_nested_models)
    
#     return all_nested_models
    
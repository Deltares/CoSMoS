# -*- coding: utf-8 -*-
"""
Created on Tue May 18 12:00:56 2021

@author: ormondt
"""

import os
import toml
from cht_utils import fileops as fo

class Station():
    """Initialize single observation station.
    """    
    def __init__(self):
        
        self.name      = None
        self.coops_id  = None 
        self.ndbc_id   = None 
        self.iho_id    = None
        self.id        = None 
        self.long_name = None
        self.longitude = None
        self.latitude  = None
        self.type      = None
        self.mllw      = None
        self.water_level_correction = 0.0
        self.file_name = None
        self.upload    = True
        self.hat       = None

class Stations():
    """Cosmos observation stations.
    """
    def __init__(self):

        self.station = []
        self.station_set = {} # Contains a list of stations (e.g. self.station_set['iho'] = [station1, station2, ...])

    def read_all(self):
        """Read cosmos observation stations from observation station xml file.
        """
        from .cosmos_main import cosmos

        file_list = fo.list_files(os.path.join(cosmos.config.path.stations,
                                               "*.toml"))
        for file_name in file_list:

            station_set_name = os.path.basename(file_name).replace(".toml", "")
            self.station_set[station_set_name] = read_station_set(file_name)

    def find_by_name(self, name):      
        """Find station name in station list.
        """
        for station_set in self.station_set.values():
            for station in station_set:
                if station.name.lower() == name:
                    return station
    
        return None

def read_station_set(file_name):
    """Read cosmos observation stations from observation station toml file."""

    toml_dict = toml.load(file_name)

    station_list = []

    for toml_stat in toml_dict['station']:

        station = Station()      
        station.name      = toml_stat['name']
        if "longname" in toml_stat:
            station.long_name = toml_stat['longname']
        elif "long_name" in toml_stat:
            station.long_name = toml_stat['long_name']
        else:
            station.long_name = toml_stat['name']
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
        if "iho_id" in toml_stat:
            station.iho_id = toml_stat['iho_id']
            station.id     = toml_stat['iho_id']
        if "ndbc_id" in toml_stat:
            station.ndbc_id = toml_stat['ndbc_id']
            station.id      = toml_stat['ndbc_id']
        if "id" in toml_stat:
            station.id = toml_stat['id']
        if "hat" in toml_stat:
            station.hat = toml_stat['hat']
            
        station.file_name = os.path.basename(file_name)    

        station_list.append(station)

    return station_list

    # def find_by_file(self, name):
    #     """Find station filename.
    #     """

    #     station_list = []
        
    #     for station in self.station:
    #         if station.file_name.lower() == name:
    #             station_list.append(station)

    #     return station_list
    
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
    
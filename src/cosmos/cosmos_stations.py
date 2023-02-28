# -*- coding: utf-8 -*-
"""
Created on Tue May 18 12:00:56 2021

@author: ormondt
"""

import os

from cht.misc import xmlkit as xml
from cht.misc import fileops as fo

class Station():
    
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

    def __init__(self):

        self.station = []                 

    def read(self):

        from .cosmos import cosmos

        file_list = fo.list_files(os.path.join(cosmos.config.path.stations,
                                               "*.xml"))
        
        for file_name in file_list:

            xml_obj = xml.xml2obj(file_name)

            for xml_stat in xml_obj.station:

                station = Station()      
                station.name      = xml_stat.name[0].value
                station.long_name = xml_stat.longname[0].value
                station.longitude = xml_stat.longitude[0].value
                station.latitude  = xml_stat.latitude[0].value
                station.type      = xml_stat.type[0].value
                if hasattr(xml_stat, "water_level_correction"):
                    station.water_level_correction = xml_stat.water_level_correction[0].value
                if hasattr(xml_stat, "MLLW"):
                    station.mllw = xml_stat.MLLW[0].value                
                if hasattr(xml_stat, "coops_id"):
                    station.coops_id = xml_stat.coops_id[0].value
                    station.id       = xml_stat.coops_id[0].value
                if hasattr(xml_stat, "ndbc_id"):
                    station.ndbc_id = xml_stat.ndbc_id[0].value
                    station.id      = xml_stat.ndbc_id[0].value
                if hasattr(xml_stat, "id"):
                    station.id = xml_stat.id[0].value
                    
                station.file_name = os.path.basename(file_name)    

                self.station.append(station) 

    def find_by_name(self, name):
        
        for station in self.station:
            if station.name.lower() == name:
                return station
    
        return None

    def find_by_file(self, name):
        
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
    
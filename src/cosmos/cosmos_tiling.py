# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 12:17:22 2021

@author: ormondt
"""
import numpy as np

from .cosmos_main import cosmos
from cht.tiling.tiling import make_png_tiles
from cht.tiling.tiling import make_floodmap_tiles

# class CoSMoS_TileLayer:
#     def __init__(self, name, long_name):
        
#         self.meta_data = {}
#         self.meta_data["name"]        = name
#         self.meta_data["long_name"]   = long_name
#         self.meta_data["zoom_range"]  = [0, 23]
#         self.meta_data["value_range"] = [999.0, -999.0]
#         self.meta_data["time"]        = []
#         time = {}
#         time["time_range"]  = []
#         time["time"]        = None
#         time["path_name"]   = None
#         time["time_string"] = None        
#         self.meta_data["time"].append(time)
        
tile_layer = {}

def make_flood_map_tiles(zsmax, index_path, topo_path, flood_map_path,
                         water_level_correction=0.0):

    # Difference between MSL and NAVD88 (used in topo data)
    zsmax += water_level_correction

    mp = next((x for x in cosmos.config.map_contours if x["name"] == "flood_map"), None)    
    color_values = mp["contours"]

    make_floodmap_tiles(zsmax, index_path, flood_map_path, topo_path,
                   option="deterministic",
                   color_values=color_values,
                   zoom_range=[0, 13],
                   zbmax=1.0,
                   quiet=True)

def make_wave_map_tiles(hm0max, index_path, wave_map_path, contour_set):

    mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)
    
    if mp is not None:
        color_values = mp["contours"]    
        make_png_tiles(hm0max, index_path, wave_map_path,
                       color_values=color_values,
                       zoom_range=[0, 9],
                       quiet=True)

def make_precipitation_tiles(pcum, index_path, p_map_path, contour_set):
    
    pcum[np.where(pcum<1.0)] = np.nan

    mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)
    
    if mp is not None:
        color_values = mp["contours"]    
        make_png_tiles(pcum, index_path, p_map_path,
                       color_values=color_values,
                       zoom_range=[0, 10],
                       quiet=True)

def make_sedero_tiles(sedero, index_path, sedero_map_path):

    mp = next((x for x in cosmos.config.map_contours if x["name"] == "sedero"), None)
    
    if mp is not None:
        color_values = mp["contours"]    
        make_png_tiles(sedero, index_path, sedero_map_path,
                       color_values=color_values,
                       zoom_range=[0, 16],
                       quiet=True)
        
def make_bedlevel_tiles(bedlevel, index_path, bedlevel_map_path):

    mp = next((x for x in cosmos.config.map_contours if x["name"] == "bed_levels"), None)
    
    if mp is not None:
        color_values = mp["contours"]    
        make_png_tiles(bedlevel, index_path, bedlevel_map_path,
                       color_values=color_values,
                       zoom_range=[0, 16],
                       quiet=True)

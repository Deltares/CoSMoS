# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os
# from matplotlib import cm
# import numpy as np
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

class Configuration:
    def __init__(self):        
        self.path           = Path()
        self.model_database = ModelDatabase()
        self.meteo_database = MeteoDatabase()
        self.conda          = Conda()
        self.executables    = Executables()
        self.webserver      = WebServer()
        self.webviewer      = WebViewer()
        self.cycle          = Cycle()
        self.kwargs         = {}
    
    def set(self, **kwargs):

        from .cosmos import cosmos
                
        if kwargs:
            self.kwargs = kwargs

        self.path.config    = os.path.join(self.path.main, "configuration")     
        self.path.jobs      = os.path.join(self.path.main, "jobs")
        self.path.stations  = os.path.join(self.path.config, "stations")
        self.path.scenarios = os.path.join(self.path.main, "scenarios")

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


    def read_config_file(self):
        
        config_file = os.path.join(self.path.config,
                                   self.file_name)     

        # Read config file        
        config_dict = toml.load(config_file)
        
        # Turn into object        
        for key in config_dict:
            obj = getattr(self, key)
            for key, value in config_dict[key].items():
                setattr(obj, key, value)
        
        
        # # Map contours
        # contour_file = os.path.join(config_path, "map_contours.xml")
        # xml_obj = xml.xml2obj(contour_file)
        # cosmos.config.map_contours = []
        # maps = xml_obj.tile_map
        # for tm in maps:
        #     map_type = {}
        #     map_type["name"] = tm.name
        #     map_type["string"] = tm.legend_text[0].value
        #     map_type["contours"] = []
        #     if not hasattr(tm, "scale"):
        #         scale = "linear"
        #     else:
        #         scale = tm.scale[0].value
            
        #     if hasattr(tm, "contour"):
    
        #         # Contours are provided
    
        #         for c in tm.contour:
        #             cnt = {}
        #             cnt["string"] = c.legend_text[0].value
        #             cnt["lower_value"] = c.lower[0].value
        #             cnt["upper_value"] = c.upper[0].value
        #             cnt["rgb"]   = c.rgb[0].value
        #             cnt["hex"]   = rgb2hex(tuple(cnt["rgb"]))
                    
        #             map_type["contours"].append(cnt)
        #     else:
    
        #         # Contours from contour map in config folder
    
        #         filename = os.path.join(config_path, tm.color_map[0].value + ".txt")
    
        #         vals  = np.loadtxt(filename)
        #         nrows = np.shape(vals)[0]
        #         ncols = np.shape(vals)[1]
        #         if ncols==4:
        #             v = np.squeeze(vals[:,0])
        #             r = np.squeeze(vals[:,1])
        #             g = np.squeeze(vals[:,2])
        #             b = np.squeeze(vals[:,3])
        #         else:    
        #             v = np.arange(0.0, 1.000001, 1.0/(nrows-1))
        #             r = np.squeeze(vals[:,0])
        #             g = np.squeeze(vals[:,1])
        #             b = np.squeeze(vals[:,2])
                    
        #         if scale == "linear":    
                        
        #             zmin = tm.lower[0].value
        #             zmax = tm.upper[0].value
        #             step = tm.step[0].value
        #             nsteps = round((zmax-zmin)/step + 2)    
                    
        #             for i in range(nsteps):
                        
        #                 # Interpolate
        #                 zl = zmin + (i - 1)*step
        #                 zu = zl + step
        #                 z  = i/((nsteps - 1)*1.0)
        #                 rr = round(np.interp(z, v, r))
        #                 gg = round(np.interp(z, v, g))
        #                 bb = round(np.interp(z, v, b))                
        #                 rgb = [rr, gg, bb]
        
        #                 cnt={}
        #                 if i==0:
        #                     cnt["string"] = "< " + str(zmin)
        #                     cnt["lower_value"] = -1.0e6
        #                     cnt["upper_value"] = zu
        #                 elif i==nsteps - 1:
        #                     cnt["string"] = "> " + str(zmax)
        #                     cnt["lower_value"] = zl
        #                     cnt["upper_value"] = 1.0e6
        #                 else: 
        #                     cnt["string"] = str(zl) + " - " + str(zu)                    
        #                     cnt["lower_value"] = zl
        #                     cnt["upper_value"] = zu
        #                 cnt["rgb"]   = rgb
        #                 cnt["hex"]   = rgb2hex(tuple(rgb))
        
        #                 map_type["contours"].append(cnt)
                    
        #         else:
                    
        #             # Logarithmic
    
        #             zmin = tm.lower[0].value
        #             zmax = tm.upper[0].value
    
        #             if scale == "log125":
        #                 nit = 10
        #                 zz  = np.zeros(nit*3)
        #                 k = -1
        #                 for i in range(nit):
        #                     k = k + 1
        #                     if i==0:
        #                         zz[k] = 1.0e-4
        #                     else:    
        #                         zz[k] = zz[k - 1] * 2                        
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 2
        #                     k = k + 1
        #                     zz[k] = zz[k - 1]*2.5
        #             elif scale == "log16":       
        #                 nit = 10
        #                 zz  = np.zeros(nit*5)
        #                 k = -1
        #                 for i in range(nit):
        #                     k = k + 1
        #                     # 0.1
        #                     if i==0:
        #                         zz[k] = 1.0e-4
        #                     else:    
        #                         zz[k] = zz[k - 1] * 100 / 65                        
        #                     k = k + 1
        #                     # 0.15
        #                     zz[k] = zz[k - 1] * 3 / 2
        #                     k = k + 1
        #                     # 0.25
        #                     zz[k] = zz[k - 1]*5/3
        #                     k = k + 1
        #                     # 0.40
        #                     zz[k] = zz[k - 1]*8/5
        #                     k = k + 1
        #                     # 0.65
        #                     zz[k] = zz[k - 1]*65/40
        #             elif scale == "log16":       
        #                 nit = 10
        #                 zz  = np.zeros(nit*5)
        #                 k = -1
        #                 for i in range(nit):
        #                     k = k + 1
        #                     # 0.1
        #                     if i==0:
        #                         zz[k] = 1.0e-4
        #                     else:    
        #                         zz[k] = zz[k - 1] * 100 / 65                        
        #                     k = k + 1
        #                     # 0.15
        #                     zz[k] = zz[k - 1] * 3 / 2
        #                     k = k + 1
        #                     # 0.25
        #                     zz[k] = zz[k - 1]*5/3
        #                     k = k + 1
        #                     # 0.40
        #                     zz[k] = zz[k - 1]*8/5
        #                     k = k + 1
        #                     # 0.65
        #                     zz[k] = zz[k - 1]*65/40
        #             elif scale == "log121":
        #                 #1 1.2 1.5 1.8 2.2 2.6 3.2 3.8 4.6 5.5 6.8 8.2 10
        #                 nit = 10
        #                 zz  = np.zeros(nit*12)
        #                 k = -1
        #                 for i in range(nit):
        #                     k = k + 1
        #                     # 0.1
        #                     if i==0:
        #                         zz[k] = 1.0e-4
        #                     else:    
        #                         zz[k] = zz[k - 1] * 50 / 41                        
        #                     # 1.2
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 6 / 5 
        #                     # 1.5
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 5 / 4 
        #                     # 1.8
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 6 / 5 
        #                     # 2.2
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 11 / 9
        #                     # 2.6
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 13 / 11
        #                     # 3.2
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 16 / 13
        #                     # 3.8
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 19 / 16
        #                     # 4.6
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 23 / 19
        #                     # 5.5
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 55 / 46
        #                     # 6.8
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 68 / 55
        #                     # 8.2
        #                     k = k + 1
        #                     zz[k] = zz[k - 1] * 41 / 34
    
                        
        #             i0 = np.where(zz>=zmin - 1.0e-6)[0][0]
        #             i1 = np.where(zz>=zmax - 1.0e-6)[0][0]
                    
        #             nsteps = i1 - i0 + 1
                    
        #             k = -1
        #             for i in range(i0, i1 + 1):
    
        #                 k = k + 1
                        
        #                 # Interpolate
        #                 z  = k/((nsteps - 1)*1.0)
        #                 rr = round(np.interp(z, v, r))
        #                 gg = round(np.interp(z, v, g))
        #                 bb = round(np.interp(z, v, b))                
        #                 rgb = [rr, gg, bb]
        
        #                 # cnt={}
        #                 # if k==0:
        #                 #     cnt["string"] = "< " + str(zmin)
        #                 #     cnt["lower_value"] = -1.0e6
        #                 #     cnt["upper_value"] = zz[i]
        #                 # elif i==nsteps - 1:
        #                 #     cnt["string"] = "> " + str(zmax)
        #                 #     cnt["lower_value"] = zz[i]
        #                 #     cnt["upper_value"] = 1.0e6
        #                 # else: 
        #                 #     cnt["string"] = str(zz[i]) + " - " + str(zz[i + 1])                    
        #                 #     cnt["lower_value"] = zz[i]
        #                 #     cnt["upper_value"] = zz[i + 1]
        #                 cnt={}
        #                 if k==0:
        #                     cnt["string"] = "< " + f"{zmin:.1f}"
        #                     cnt["lower_value"] = -1.0e6
        #                     cnt["upper_value"] = zz[i]
        #                 elif k==nsteps - 1:
        #                     cnt["string"] = "> " +  f"{zmax:.1f}"
        #                     cnt["lower_value"] = zz[i]
        #                     cnt["upper_value"] = 1.0e6
        #                 else: 
        #                     cnt["string"] = f"{zz[i - 1]:.1f}" + " - " + f"{zz[i]:.1f}"                   
        #                     cnt["lower_value"] = zz[i - 1]
        #                     cnt["upper_value"] = zz[i]
        #                 cnt["rgb"]   = rgb
        #                 cnt["hex"]   = rgb2hex(tuple(rgb))
        
        #                 map_type["contours"].append(cnt)
    
                
        #         map_type["contours"] = map_type["contours"][::-1]
                
        #     cosmos.config.map_contours.append(map_type)    

# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:38:37 2021

@author: ormondt
"""

import os
from pyproj import CRS
from pyproj import Transformer
import copy
from matplotlib import path   
import pandas as pd                     
from scipy import interpolate
import numpy as np
import toml
import geopandas as gpd
import shapely

from .cosmos_main import cosmos
from .cosmos_cluster import cluster_dict as cluster

from cht.nesting.nest2 import nest2
import cht.misc.fileops as fo
from cht.misc.misc_tools import dict2yaml

class Model:
    """Read generic model data from toml file, prepare model run paths, and submit jobs.

    """
    def __init__(self):
        """Initialize model attributes described in model.toml file.
        """
 
        self.flow               = False
        self.wave               = False
        self.priority           = 10    
        self.flow_nested        = None
        self.wave_nested        = None
        self.bw_nested          = None
        self.flow_nested_name   = None
        self.wave_nested_name   = None
        self.bw_nested_name     = None
        self.nested_flow_models = []
        self.nested_wave_models = []
        self.nested_bw_models = []
        self.flow_spinup_time   = 0.0
        self.wave_spinup_time   = 0.0
        self.xlim               = None
        self.ylim               = None
        self.flow_restart_file  = None
        self.wave_restart_file  = None
        self.vertical_reference_level_name = "MSL"
        self.vertical_reference_level_difference_with_msl = 0.0
        self.boundary_water_level_correction = 0.0
        self.station            = []
        self.meteo_subset       = None
        self.meteo_spiderweb    = None
        self.meteo_dataset      = None
        self.meteo_wind                 = True
        self.meteo_atmospheric_pressure = True
        self.meteo_precipitation        = True
        self.runid              = None
        self.polygon            = None
        self.make_flood_map     = False
        self.make_wave_map      = False
        self.make_water_level_map = False
        self.make_precipitation_map = False
        self.make_sedero_map    = False
        self.sa_correction      = None
        self.ssa_correction     = None
        self.wave               = False
        self.mhhw               = 0.0
        self.cluster            = None
        self.boundary_twl_treshold = 999.0
        self.peak_boundary_twl     = None
        self.peak_boundary_time    = None
        self.zb_deshoal         = None
        self.ensemble           = False

    def read_generic(self):
        """Read model attributes from model.toml file.

        See Also
        --------
        cosmos.cosmos_scenario.Scenario
        cosmos.cosmos_model_loop.ModelLoop
        """

        mdl_dict = toml.load(self.file_name)

        # Turn into object        
        for key, value in mdl_dict.items():
            setattr(self, key, value)

        self.flow_nested_name = self.flow_nested    
        self.wave_nested_name = self.wave_nested    
        self.bw_nested_name   = self.bw_nested    

        self.crs = CRS(self.crs)
                
        # Read polygon around model (should really use geojson file for this)
        polygon_file  = os.path.join(self.path, "misc", self.name + ".txt")
        if os.path.exists(polygon_file):
            df = pd.read_csv(polygon_file, index_col=False, header=None,
                 delim_whitespace=True, names=['x', 'y'])
            xy = df.to_numpy()
            self.polygon = path.Path(xy)
            if not self.xlim:
                self.xlim = [self.polygon.vertices.min(axis=0)[0],
                             self.polygon.vertices.max(axis=0)[0]]
                self.ylim = [self.polygon.vertices.min(axis=0)[1],
                             self.polygon.vertices.max(axis=0)[1]]
            # Make gdf with outline 
            geom = shapely.geometry.Polygon(np.squeeze(xy))
            self.outline = gpd.GeoDataFrame({"geometry": [geom]}).set_crs(self.crs).to_crs(4326)   
           
        # Stations
        if self.station:
            station_list = self.station
            self.station = []
            for istat in range(len(station_list)):                
                # Find matching stations from complete stations list
                name = station_list[istat]
                self.add_stations(name)

    def write_config_yml(self):            
        # Write config file to be used in run_job.py
        config = {}
        config["model"] = self.name
        config["type"] = self.type
        config["region"] = self.region
        config["scenario"] = cosmos.scenario_name
        config["cycle"]    = cosmos.cycle_string
        config["ensemble"] = self.ensemble
        config["run_mode"] = cosmos.config.run.run_mode
        config["vertical_reference_level_difference_with_msl"] = self.vertical_reference_level_difference_with_msl

        ## INPUT for nesting
        if self.ensemble:
            config["spw_path"] = cosmos.scenario.cycle_track_ensemble_spw_path
        if cosmos.config.run.run_mode == "cloud":
            config["cloud"] = {}
            config["cloud"]["host"] = cosmos.config.cloud_config.host
            config["cloud"]["access_key"] = cosmos.config.cloud_config.access_key
            config["cloud"]["secret_key"] = cosmos.config.cloud_config.secret_key
            config["cloud"]["region"] = cosmos.config.cloud_config.region
            config["cloud"]["token"] = cosmos.config.cloud_config.token
            config["cloud"]["namespace"] = cosmos.config.cloud_config.namespace
        if self.flow_nested:
            # Water level forcing
            config["flow_nested"] = {}
            config["flow_nested"]["overall_model"] = self.flow_nested.name
            config["flow_nested"]["overall_type"]  = self.flow_nested.type
            config["flow_nested"]["overall_path"]  = self.flow_nested.cycle_output_path
            # This bit is needed for cloud mode (file needs to be downloaded from S3)
            if self.flow_nested.type == "sfincs":
                file_name = "sfincs_his.nc"
            elif self.flow_nested.type == "xbeach":
                file_name = "xbeach_his.nc"
            elif self.flow_nested.type == "delft3dfm":
                file_name = "flow_his.nc"
            elif self.flow_nested.type == "delft3d":
                file_name = "delft3d_his.nc"
            config["flow_nested"]["overall_file"]  = file_name
            config["flow_nested"]["boundary_water_level_correction"] = self.boundary_water_level_correction
        if self.wave_nested:
            # Wave forcing
            config["wave_nested"] = {}
            config["wave_nested"]["overall_model"] = self.wave_nested.name
            config["wave_nested"]["overall_type"]  = self.wave_nested.type
            config["wave_nested"]["overall_path"]  = self.wave_nested.cycle_output_path
            # This bit is needed for cloud mode (file needs to be downloaded from S3)
            if self.wave_nested.type == "hurrywave":
                file_name = "hurrywave_sp2.nc"
            config["wave_nested"]["overall_file"]  = file_name
        if self.bw_nested: 
            # Beware forcing
            config["bw_nested"] = {}
            config["bw_nested"]["overall_model"] = self.bw_nested.name
            config["bw_nested"]["overall_type"]  = self.bw_nested.type
            config["bw_nested"]["overall_path"]  = self.bw_nested.cycle_output_path
            config["bw_nested"]["overall_crs"]   = self.bw_nested.crs.to_epsg()
            config["bw_nested"]["detail_crs"]   = self.crs.to_epsg()
        if self.type == "xbeach":
            config["xbeach"] = {}
            config["xbeach"]["tref"] = self.domain.tref.strftime("%Y%m%d %H%M%S")
            config["xbeach"]["tstop"] = self.domain.tstop.strftime("%Y%m%d %H%M%S")
            config["xbeach"]["flow_nesting_points"] = self.flow_nesting_points
            config["xbeach"]["wave_nesting_point"] = self.wave_nesting_point
            config["xbeach"]["zb_deshoal"] = self.domain.zb_deshoal

        # OUTPUT for webviewer
        if cosmos.config.run.make_flood_maps and self.make_flood_map:
            config["flood_map"] = {}
            if self.ensemble:
                name = "flood_map_90"
            else:
                name = "flood_map"    
            config["flood_map"]["name"] = name
            if cosmos.config.run.run_mode == "cloud":
                config["flood_map"]["png_path"]   = "/output"
                config["flood_map"]["index_path"] = "/tiles/indices"
                config["flood_map"]["topo_path"]  = "/tiles/topobathy"
                config["flood_map"]["zsmax_path"]  = "/input"
            else:
                config["flood_map"]["png_path"]   = os.path.join(cosmos.config.webviewer.data_path)
                config["flood_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
                config["flood_map"]["topo_path"]  = os.path.join(self.path, "tiling", "topobathy")
                config["flood_map"]["zsmax_path"]  = "."
            config["flood_map"]["start_time"] = cosmos.cycle
            config["flood_map"]["stop_time"]  = cosmos.stop_time
            config["flood_map"]["interval"] = cosmos.config.webviewer.tile_layer["flood_map"]["interval"]
            config["flood_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["flood_map"]["color_map"]]
        if cosmos.config.run.make_water_level_maps and self.make_water_level_map:
            config["water_level_map"] = {}
            if self.ensemble:
                name = "water_level_90"
            else:
                name = "water_level"    
            config["water_level_map"]["name"] = name
            if cosmos.config.run.run_mode == "cloud":
                config["water_level_map"]["png_path"]   = "/output"
                config["water_level_map"]["index_path"] = "/tiles/indices"
                config["water_level_map"]["topo_path"]  = "/tiles/topobathy"
                config["water_level_map"]["zsmax_path"]  = "/input"
            else:
                config["water_level_map"]["png_path"]   = os.path.join(cosmos.config.webviewer.data_path)
                config["water_level_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
                config["water_level_map"]["topo_path"]  = os.path.join(self.path, "tiling", "topobathy")
                config["water_level_map"]["zsmax_path"]  = "."
            config["water_level_map"]["start_time"] = cosmos.cycle
            config["water_level_map"]["stop_time"]  = cosmos.stop_time
            config["water_level_map"]["interval"] = cosmos.config.webviewer.tile_layer["water_level_map"]["interval"]
            config["water_level_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["water_level_map"]["color_map"]]
        if cosmos.config.run.make_wave_maps and self.make_wave_map:
            config["hm0_map"] = {}
            if self.ensemble:
                name = "hm0_90"
            else:
                name = "hm0"
            config["hm0_map"]["name"]       = name
            if cosmos.config.run.run_mode == "cloud":
                config["hm0_map"]["png_path"]   = "/output"
                config["hm0_map"]["index_path"] = "/tiles/indices"
                config["hm0_map"]["output_path"]  = "/input"
            else:
                config["hm0_map"]["png_path"]   = os.path.join(cosmos.config.webviewer.data_path)
                config["hm0_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
                config["hm0_map"]["output_path"]  = "."
            config["hm0_map"]["start_time"] = cosmos.cycle
            config["hm0_map"]["stop_time"]  = cosmos.stop_time
            config["hm0_map"]["interval"] = cosmos.config.webviewer.tile_layer["hm0"]["interval"]
            config["hm0_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["hm0"]["color_map"]]
        if cosmos.config.run.make_sedero_maps and self.make_sedero_map:
            config["sedero_map"] = {}
            name = "sedero" 
            config["sedero_map"]["name"] = name
            if cosmos.config.run.run_mode == "cloud":
                config["sedero_map"]["png_path"]   = "/output"
                config["sedero_map"]["index_path"] = "/tiles/indices"
                config["sedero_map"]["output_path"] = "/input"
            else:
                config["sedero_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
                config["sedero_map"]["png_path"] = os.path.join(cosmos.config.webviewer.data_path)
                config["sedero_map"]["output_path"] = "."
            config["sedero_map"]["start_time"] = self.domain.tref
            config["sedero_map"]["stop_time"]  = self.domain.tstop
            config["sedero_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["sedero"]["color_map"]]    
            config["sedero_map"]["color_map_zb"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["bed_levels"]["color_map"]]    
        if cosmos.config.run.make_meteo_maps and self.make_precipitation_map:
            config["precipitation_map"] = {}
            if self.ensemble:
                name = "precipitation_90"
            else:
                name = "precipitation" 
            config["precipitation_map"]["name"] = name
            if cosmos.config.run.run_mode == "cloud":
                config["precipitation_map"]["png_path"]   = "/output"
                config["precipitation_map"]["index_path"] = "/tiles/indices"
                config["precipitation_map"]["output_path"] = "/input"
            else:
                config["precipitation_map"]["index_path"] = os.path.join(self.path, "tiling", "indices")
                config["precipitation_map"]["png_path"] = os.path.join(cosmos.config.webviewer.data_path)
                config["precipitation_map"]["output_path"] = "."
            config["precipitation_map"]["start_time"] = cosmos.cycle
            config["precipitation_map"]["stop_time"]  = cosmos.stop_time  
            config["precipitation_map"]["color_map"]  = cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["precipitation"]["color_map"]]

        dict2yaml(os.path.join(self.job_path, "config.yml"), config)
        
    def set_paths(self):
        """Set model paths (input, output, figures, restart, job).

        See Also
        --------
        cosmos.cosmos_main_loop.MainLoop
        """        
        # First model and restart folders if necessary

        cycle_path      = cosmos.scenario.cycle_path
        restart_path    = cosmos.scenario.restart_path
#        timeseries_path = cosmos.scenario.cycle_timeseries_path
        # region          = self.region
        # tp              = self.type
        name            = self.name

        # # Path with model results in cycle
        # self.cycle_path = os.path.join(cycle_path,
        #                                "models", region, tp, name)
        # self.cycle_input_path   = os.path.join(cycle_path, "models", region, tp, name, "input")
        # self.cycle_output_path  = os.path.join(cycle_path, "models", region, tp, name, "output")
        # self.cycle_figures_path = os.path.join(cycle_path, "models", region, tp, name, "figures")
        # self.cycle_post_path    = os.path.join(cycle_path, "models", region, tp, name, "timeseries")
        
        # # Restart paths
        # self.restart_flow_path = os.path.join(restart_path,
        #                                       region, tp, name, "flow")
        # self.restart_wave_path = os.path.join(restart_path,
        #                                       region, tp, name, "wave")


        # Path with model results in cycle
        self.cycle_path         = os.path.join(cycle_path, "models", name)
        self.cycle_input_path   = os.path.join(cycle_path, "models", name, "input")
        self.cycle_output_path  = os.path.join(cycle_path, "models", name, "output")
        self.cycle_figures_path = os.path.join(cycle_path, "models", name, "figures")
        self.cycle_post_path    = os.path.join(cycle_path, "models", name, "timeseries")
        
        # Restart paths (use deterministic name for restart files)
        self.restart_flow_path = os.path.join(restart_path, self.deterministic_name, "flow")
        self.restart_wave_path = os.path.join(restart_path, self.deterministic_name, "wave")

        # Model folder in the jobs folder
        # self.job_path = os.path.join(cosmos.config.path.jobs,
        #                              cosmos.scenario.name,
        #                              self.name)        
        self.job_path = self.cycle_path  

    def make_paths(self):
        # Make model cycle paths
        fo.mkdir(self.cycle_path)
        # fo.mkdir(self.cycle_input_path)
        # fo.mkdir(self.cycle_output_path)
        # fo.mkdir(self.cycle_figures_path)
        # fo.mkdir(self.cycle_post_path)
        fo.mkdir(self.restart_flow_path)
        fo.mkdir(self.restart_wave_path)

    def get_nested_models(self):
        """Get which model the current model is nested in. 
        """        
        if self.flow_nested_name:
            # Look up model from which it gets it boundary conditions
            for model2 in cosmos.scenario.model:
                if model2.name == self.flow_nested_name:
                    self.flow_nested = model2
                    model2.nested_flow_models.append(self)
                    break
        if self.wave_nested_name:
            # Look up model from which it gets it boundary conditions
            for model2 in cosmos.scenario.model:
                if model2.name == self.wave_nested_name:
                    self.wave_nested = model2
                    model2.nested_wave_models.append(self)
                    break
        if self.bw_nested_name:
            # Look up model from which it gets it boundary conditions
            for model2 in cosmos.scenario.model:
                if model2.name == self.bw_nested_name:
                    self.bw_nested = model2
                    model2.nested_bw_models.append(self)
                    break

    def get_all_nested_models(self, tp, all_nested_models=None):
        """Return a list of all models nested in this model.
        """        
        # def get_all_nested_models(self, tp, all_nested_models=[]):
        # don't define empty list as default ! (https://nikos7am.com/posts/mutable-default-arguments/)
        # Return a list of all models nested in this model

        if all_nested_models is None:
            all_nested_models = []        
        
        if tp == "flow":
            for mdl in self.nested_flow_models:
                all_nested_models.append(mdl)
                if mdl.nested_flow_models:
                    all_nested_models = mdl.get_all_nested_models("flow",
                                        all_nested_models=all_nested_models)
        
        if tp == "wave":
            for mdl in self.nested_wave_models:
                all_nested_models.append(mdl)
                if mdl.nested_wave_models:
                    all_nested_models = mdl.get_all_nested_models("wave",
                                        all_nested_models=all_nested_models)
        
        return all_nested_models
        
    def add_stations(self, name):
        """Add stations that are located within this model.

        Parameters
        ----------
        name : str
            station file name or station name
        """        
        wgs84 = CRS.from_epsg(4326)
        transformer = Transformer.from_crs(wgs84, self.crs, always_xy=True)
        
        if name[-4:].lower() == "toml":

            # Get all stations in file
            stations = cosmos.config.stations.find_by_file(name)

            for st in stations:

                station = copy.copy(st)
                station.longitude_model = station.longitude
                station.latitude_model  = station.latitude
                
                x, y = transformer.transform(station.longitude_model,
                                             station.latitude_model)
                station.x = x
                station.y = y
                
                # Check whether this station lies with model domain
                
                if self.polygon:                            
                    if not self.polygon.contains_points([(x, y)])[0]:
                        # On to the next station
                        continue

                self.station.append(station)
                                        
        else:

            station = copy.copy(cosmos.config.stations.find_by_name(name))

            station.longitude_model = station.longitude
            station.latitude_model  = station.latitude
            
            x, y = transformer.transform(station.longitude_model,
                                         station.latitude_model)
            station.x = x
            station.y = y

            self.station.append(station)
            
    def get_peak_boundary_conditions(self):
            """Get boundary conditions from overall model and define peak.
            """      
            # Water level boundary conditions

            # Get boundary conditions from overall model (Nesting 2)
            zcor = self.boundary_water_level_correction - self.vertical_reference_level_difference_with_msl                    

            if self.type == "xbeach":
                self.domain.tref  = self.flow_start_time
                self.domain.tstop = self.flow_stop_time

            z_max = nest2(self.flow_nested.domain,
                          self.domain,
                          output_path=self.flow_nested.cycle_output_path,
                          boundary_water_level_correction=zcor,
                          return_maximum=True)
            t = z_max.index
            z = z_max.values

            # Wave boundary conditions
            if self.wave_nested:
    
                # Get boundary conditions from overall model (Nesting 2)
                hm0_max = nest2(self.wave_nested.domain,
                                self.domain,
                                output_path=self.wave_nested.cycle_output_path,
                                option="timeseries",
                                return_maximum=True)

                # Interpolate to flow boundary times
                flow_secs = z_max.index.values.astype(float)
                wave_secs = hm0_max.index.values.astype(float)
                f = interpolate.interp1d(wave_secs, hm0_max.values)
                hm0 = f(flow_secs)
                hm0 = np.nan_to_num(hm0)
                            
            else:
                hm0 = np.zeros(np.size(z))

            # Estimate total water level above MHHW with tide + surge + 0.2*Hm0
            twl = z + cluster[self.cluster].hm0fac*hm0 - self.mhhw 
            
            # Index of peak
            imax = np.argmax(twl)
            
            self.peak_boundary_twl  = twl[imax]
            self.peak_boundary_time = t[imax].to_pydatetime()

    def set_stations_to_upload(self):
        all_nested_models = self.get_all_nested_models("flow")
        if self.type=='beware':
            for station in self.station:
                station.upload = False 

        if all_nested_models:
            all_nested_stations = []
            if all_nested_models[0].type == 'beware':
                all_nested_models= [self]
                bw=1
            else:
                bw=0
            for mdl in all_nested_models:
                for st in mdl.station:
                    all_nested_stations.append(st.name)
            for station in self.station:
                if station.type == "tide_gauge":
                    if station.name in all_nested_stations and bw==0:                            
                        station.upload = False 

        all_nested_models = self.get_all_nested_models("wave")
        if all_nested_models:
            all_nested_stations = []
            if all_nested_models[0].type == 'beware':
                all_nested_models= [self]
                bw=1
            else:
                bw=0
            for mdl in all_nested_models:
                for st in mdl.station:
                    all_nested_stations.append(st.name)
            for station in self.station:
                if station.type == "wave_buoy":
                    if station.name in all_nested_stations and bw==0:
                        station.upload = False 

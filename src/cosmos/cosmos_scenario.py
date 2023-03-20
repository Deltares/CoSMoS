# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:29:26 2021

@author: ormondt
"""
import os

from .cosmos_main import cosmos
from .cosmos_cluster import cluster_dict
from .cosmos_cluster import Cluster

from cht.misc import fileops as fo
from cht.misc import xmlkit as xml

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
        
    def read(self):
        
        # Set paths
        self.cycle_path            = os.path.join(self.path, cosmos.cycle_string)
        self.cycle_models_path     = os.path.join(self.path, cosmos.cycle_string, "models")
        self.cycle_tiles_path      = os.path.join(self.path, cosmos.cycle_string, "tiles")
        self.cycle_job_list_path   = os.path.join(self.path, cosmos.cycle_string, "job_list")
        self.restart_path          = os.path.join(self.path, "restart")
        self.timeseries_path       = os.path.join(self.path, "timeseries")
        self.cycle_timeseries_path = os.path.join(self.path, "timeseries", cosmos.cycle_string)

        xml_obj = xml.xml2obj(self.file_name)
        
        ### Names
        # Check if cycle is supplied (if not, this is a forecasting run)
        if hasattr(xml_obj, "longname"):
            self.long_name = xml_obj.longname[0].value
        else:
            self.long_name = self.name
            
        self.run_duration = xml_obj.runtime[0].value
        
        ### Ensemble

        if hasattr(xml_obj, "track_ensemble"):
            self.track_ensemble = xml_obj.track_ensemble[0].value
            cosmos.scenario.member_names = []
            ensemble_path = os.path.join(cosmos.config.main_path,
                                         "meteo",
                                         self.track_ensemble)

            # If nr of tracks indicated in scenario file, generate new spw files based on .cyc file in ensemble folder
            if hasattr(xml_obj, "ensemble_nrtracks"):
                fo.delete_file(fo.list_files(os.path.join(ensemble_path, "*.spw")))

                from cht.tropical_cyclone.tropical_cyclone import TropicalCyclone
                from cht.tropical_cyclone.tropical_cyclone import TropicalCycloneEnsemble
                from cht.tropical_cyclone.tropical_cyclone import holland2010, wind_radii_nederhoff
                from datetime import datetime, timedelta

                tc= TropicalCyclone()
                file_name_cyc =fo.list_files(os.path.join(ensemble_path, "*.cyc"))
                cycname = os.path.basename(file_name_cyc[0]).split('.')[0]

                tc.from_ddb_cyc(file_name_cyc[0])
                tc.account_for_forward_speed()
                tc.estimate_missing_values()
                tc.include_rainfall = True

                self.ensemble_nrtracks = xml_obj.ensemble_nrtracks[0].value
                tc2= TropicalCycloneEnsemble(name= cycname, TropicalCyclone= tc)
                tc2.tstart  = xml_obj.cycle[0].value
                tc2.tend    = xml_obj.cycle[0].value+timedelta(hours=self.run_duration)
                tc2.compute_ensemble(number_of_realizations= self.ensemble_nrtracks)

                tc2.to_shapefile(folder_path=ensemble_path)
                tc2.to_spiderweb(folder_path=ensemble_path)

            file_names = fo.list_files(os.path.join(ensemble_path, "*.spw"))

            # Loop through file names
            for file_name in file_names:                
                if file_name[-9:-4]=="00000":
                    cosmos.scenario.best_track_file = os.path.join(ensemble_path,
                                                                file_name)
                else:
                    cosmos.scenario.member_names.append(os.path.split(file_name)[1][0:-4])
        
        else:
            self.track_ensemble = None
            
        ### Meteo forcing   
        scn_meteo_dataset              = None
        scn_meteo_spiderweb            = None
        scn_meteo_wind                 = True
        scn_meteo_atmospheric_pressure = True
        scn_meteo_precipitation        = True
        scn_ensemble                   = False
        scn_make_flood_map             = True
        scn_make_wave_map              = True

        if hasattr(xml_obj, "meteo_dataset"):
            scn_meteo_dataset = xml_obj.meteo_dataset[0].value

        if hasattr(xml_obj, "meteo_spiderweb"):
            scn_meteo_spiderweb = xml_obj.meteo_spiderweb[0].value

        if hasattr(xml_obj, "wind"):
            if xml_obj.wind[0].value[0] == "y":
                scn_meteo_wind = True
            else:    
                scn_meteo_wind = False
        
        if hasattr(xml_obj, "atmospheric_pressure"):
            if xml_obj.atmospheric_pressure[0].value[0] == "y":
                scn_meteo_atmospheric_pressure = True
            else:    
                scn_meteo_atmospheric_pressure = False

        if hasattr(xml_obj, "precipitation"):
            if xml_obj.precipitation[0].value[0] == "y":
                scn_meteo_precipitation = True
            else:    
                scn_meteo_precipitation = False

        if hasattr(xml_obj, "ensemble"):
            if xml_obj.ensemble[0].value[0] == "y":
                scn_ensemble = True
            else:    
                scn_ensemble = False

        ### Web viewer
        if hasattr(xml_obj, "lon"):
            self.lon = xml_obj.lon[0].value
        if hasattr(xml_obj, "lat"):
            self.lat = xml_obj.lat[0].value
        if hasattr(xml_obj, "zoom"):
            self.zoom = xml_obj.zoom[0].value
        if hasattr(xml_obj, "observations_path"):
            self.observations_path = xml_obj.observations_path[0].value
        else:
            self.observations_path = None
        if hasattr(xml_obj, "make_flood_map"):
            if xml_obj.make_flood_map[0].value[0].lower() == "y":
                scn_make_flood_map = True
            else:    
                scn_make_flood_map = False
        if hasattr(xml_obj, "make_wave_map"):
            if xml_obj.make_wave_map[0].value[0].lower() == "y":
                scn_make_wave_map = True
            else:    
                scn_make_wave_map = False
            
        # First find all the models and store in dict models_in_scenario
        models_in_scenario = {}
        for mdl in xml_obj.model:
            
            mdl_meteo_dataset              = None
            mdl_meteo_spiderweb            = None
            mdl_meteo_wind                 = None
            mdl_meteo_atmospheric_pressure = None
            mdl_meteo_precipitation        = None
            mdl_ensemble                   = None
            mdl_make_flood_map             = None
            mdl_make_wave_map              = None
            
            # Read meteo forcing for this model (overrides values given in scenario)          
            if hasattr(mdl, "meteo_dataset"):
                mdl_meteo_dataset = mdl.meteo_dataset[0].value
            if hasattr(mdl, "meteo_spiderweb"):
                mdl_meteo_spiderweb = mdl.meteo_spiderweb[0].value
            if hasattr(mdl, "wind"):
                if mdl.wind[0].value[0] == "y":
                    mdl_meteo_wind = True
                else:    
                    mdl_meteo_wind = False            
            if hasattr(mdl, "atmospheric_pressure"):
                if mdl.atmospheric_pressure[0].value[0] == "y":
                    mdl_meteo_atmospheric_pressure = True
                else:    
                    mdl_meteo_atmospheric_pressure = False
            if hasattr(mdl, "precipitation"):
                if mdl.precipitation[0].value[0] == "y":
                    mdl_meteo_precipitation = True
                else:    
                    mdl_meteo_precipitation = False                    
            if hasattr(mdl, "ensemble"):
                if mdl.ensemble[0].value[0] == "y":
                    mdl_ensemble = True
                else:    
                    mdl_ensemble = False        

            if hasattr(mdl, "make_flood_map"):
                if mdl.make_flood_map[0].value[0].lower() == "y":
                    mdl_make_flood_map = True
                else:    
                    mdl_make_flood_map = False
            if hasattr(mdl, "make_wave_map"):
                if mdl.make_wave_map[0].value[0].lower() == "y":
                    mdl_make_wave_map = True
                else:    
                    mdl_make_wave_map = False
                                
            if hasattr(mdl, "name"):

                # Individual model

                name = mdl.name[0].value.lower()
                models_in_scenario[name] = cosmos.all_models[name]
                
                # Set default values provided for scenario as a whole
                models_in_scenario[name]["meteo_dataset"]              = scn_meteo_dataset
                models_in_scenario[name]["meteo_spiderweb"]            = scn_meteo_spiderweb
                models_in_scenario[name]["meteo_wind"]                 = scn_meteo_wind
                models_in_scenario[name]["meteo_atmospheric_pressure"] = scn_meteo_atmospheric_pressure
                models_in_scenario[name]["meteo_precipitation"]        = scn_meteo_precipitation
                models_in_scenario[name]["ensemble"]                   = scn_ensemble
                models_in_scenario[name]["make_flood_map"]             = scn_make_flood_map
                models_in_scenario[name]["make_wave_map"]              = scn_make_wave_map

                # Override if other data is provided
                if mdl_meteo_dataset:
                    models_in_scenario[name]["meteo_dataset"]              = mdl_meteo_dataset
                if mdl_meteo_spiderweb:
                    models_in_scenario[name]["meteo_spiderweb"]            = mdl_meteo_spiderweb
                if mdl_meteo_wind is True or mdl_meteo_wind is False:
                    models_in_scenario[name]["meteo_wind"]                 = mdl_meteo_wind
                if mdl_meteo_atmospheric_pressure is True or mdl_meteo_atmospheric_pressure is False:
                    models_in_scenario[name]["meteo_atmospheric_pressure"] = mdl_meteo_atmospheric_pressure
                if mdl_meteo_precipitation is True or mdl_meteo_precipitation is False:
                    models_in_scenario[name]["meteo_precipitation"]        = mdl_meteo_precipitation
                if mdl_ensemble is True or mdl_ensemble is False:
                    models_in_scenario[name]["ensemble"]             = mdl_ensemble
                if mdl_make_flood_map is True or mdl_make_flood_map is False:
                    models_in_scenario[name]["make_flood_map"]             = mdl_make_flood_map 
                if mdl_make_wave_map is True or mdl_make_wave_map is False:
                    models_in_scenario[name]["make_wave_map"]              = mdl_make_flood_map 
                    
                                    
            else:

                # Model by region and type
                
                region_list       = [] # List of regions
                type_list         = [] # List of types

                if hasattr(mdl, "region"):
                    for xml_region in mdl.region:
                        if not xml_region.value.lower() in region_list:
                            region_list.append(xml_region.value.lower())
                if hasattr(mdl, "type"):
                    for xml_type in mdl.type:                    
                        type_list.append(xml_type.value.lower())
                if hasattr(mdl, "super_region"):
                    for spr in mdl.super_region:
                        super_region_name = spr.value.lower()
                        for region in cosmos.super_region[super_region_name]:
                            if not region in region_list:
                                region_list.append(region)

                # Loop through all available models
                for name, properties in cosmos.all_models.items():
                    okay = True
                    # Filter by region
                    if region_list:
                        if not properties["region"] in region_list:
                            # Region of this model is not in region_list
                            okay = False
                            continue
                    # Filter by type
                    if type_list:
                        if not properties["type"] in type_list:
                            okay = False
                            continue
                    if okay:
                        models_in_scenario[name] = properties
                        
                        # Set default values provided for scenario as a whole
                        models_in_scenario[name]["meteo_dataset"]              = scn_meteo_dataset
                        models_in_scenario[name]["meteo_spiderweb"]            = scn_meteo_spiderweb
                        models_in_scenario[name]["meteo_wind"]                 = scn_meteo_wind
                        models_in_scenario[name]["meteo_atmospheric_pressure"] = scn_meteo_atmospheric_pressure
                        models_in_scenario[name]["meteo_precipitation"]        = scn_meteo_precipitation
                        models_in_scenario[name]["ensemble"]                   = scn_ensemble
                        models_in_scenario[name]["make_flood_map"]             = scn_make_flood_map
                        models_in_scenario[name]["make_wave_map"]              = scn_make_wave_map
        
                        # Override if other data is provided
                        if mdl_meteo_dataset:
                            models_in_scenario[name]["meteo_dataset"]              = mdl_meteo_dataset
                        if mdl_meteo_spiderweb:
                            models_in_scenario[name]["meteo_spiderweb"]            = mdl_meteo_spiderweb
                        if mdl_meteo_wind:
                            models_in_scenario[name]["meteo_wind"]                 = mdl_meteo_wind
                        if mdl_meteo_atmospheric_pressure:
                            models_in_scenario[name]["meteo_atmospheric_pressure"] = mdl_meteo_atmospheric_pressure
                        if mdl_meteo_precipitation:
                            models_in_scenario[name]["meteo_precipitation"]        = mdl_meteo_precipitation
                        if mdl_ensemble:
                            models_in_scenario[name]["ensemble"]             = mdl_ensemble
                        if mdl_make_flood_map:
                            models_in_scenario[name]["make_flood_map"]             = mdl_make_flood_map 
                        if mdl_make_wave_map:
                            models_in_scenario[name]["make_wave_map"]              = mdl_make_flood_map 
                        

        ### Add missing models
        # We know which models need to be added. Check if all models that provide boundary conditions are there as well.
                        
        ### Clear model list
        self.model = []

        # Loop through models in scenario         
        for name, properties in models_in_scenario.items():
            
            region = properties["region"]
            tp     = properties["type"]
            vsn    = "001"

            # Path where model sits in model database                        
            model_path = os.path.join(cosmos.config.main_path,
                                      "models", region, tp, name)

            file_name = os.path.join(model_path, name + ".xml")

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

            # Path in model database
            model.path = model_path
                                    
            model.name                       = name
            model.version                    = vsn
            model.region                     = region
            model.file_name                  = file_name
            model.type                       = tp
            model.meteo_dataset              = properties["meteo_dataset"]
            model.meteo_spiderweb            = properties["meteo_spiderweb"]
            model.meteo_wind                 = properties["meteo_wind"]
            model.meteo_precipitation        = properties["meteo_precipitation"]
            model.meteo_atmospheric_pressure = properties["meteo_atmospheric_pressure"]
            model.ensemble                   = properties["ensemble"]
            model.make_flood_map             = properties["make_flood_map"]
            model.make_wave_map              = properties["make_wave_map"]

            model.flow_start_time            = None
            model.flow_stop_time             = None

            # if hasattr(mdl, "tide"):
            #     tide = mdl.tide[0].value
            #     if tide == "yes":
            #         model.tide = True
            #     else:
            #         model.tide = False
            # else:
            model.tide = True

            # Read in model generic data (from xml file)
            model.read_generic()

            # # Read in model specific data (input files)
            # # Should move this bit to pre-processing of model
            model.read_model_specific()
            
            # # Overrule data in in model xml with those found in scenario xml
            # if hasattr(mdl, "boundary_water_level_correction"):
            #     model.boundary_water_level_correction = mdl.boundary_water_level_correction[0].value
            # if hasattr(mdl, "make_flood_map"):
            #     if mdl.make_flood_map[0].value[0].lower() == "y":
            #         model.make_flood_map = True
            #     else:    
            #         model.make_flood_map = False
            # if hasattr(mdl, "make_wave_map"):
            #     if mdl.make_wave_map[0].value[0].lower() == "y":
            #         model.make_wave_map = True
            #     else:    
            #         model.make_wave_map = False

            # # Additional stations
            # if hasattr(mdl, "station"):
            #     for station in mdl.station:
            #         model.add_stations(station.value[0].lower)
            
            # model.archive_path = os.path.join(model.results_path,
            #                                   "archive")        
                        
            self.model.append(model)
                
        ### Add models to clusters 
        if hasattr(xml_obj, "cluster"):
            for xml_cluster in xml_obj.cluster:
                name = xml_cluster.name[0].value.lower()
                cl = Cluster(name)
                if hasattr(xml_cluster, "run_condition"):
                    cl.run_condition = xml_cluster.run_condition[0].value
                if hasattr(xml_cluster, "topn"):
                    cl.topn = int(xml_cluster.topn[0].value)
                if hasattr(xml_cluster, "hm0fac"):
                    cl.hm0fac = float(xml_cluster.hm0fac[0].value)
                if hasattr(xml_cluster, "boundary_twl_margin"):
                    cl.boundary_twl_margin = float(xml_cluster.boundary_twl_margin[0].value)
                if hasattr(xml_cluster, "use_threshold"):
                    if xml_cluster.use_threshold[0].value == "y":
                        cl.use_threshold = True
                    else:    
                        cl.use_threshold = False                        
                if cl.run_condition == "topn":
                    cl.ready = False
                    
                # Add models to this cluster    
                region_list       = [] # List of regions
                type_list         = [] # List of types

                if hasattr(xml_cluster, "region"):
                    for xml_region in xml_cluster.region:
                        if not xml_region.value.lower() in region_list:
                            region_list.append(xml_region.value.lower())
                if hasattr(xml_cluster, "type"):
                    for xml_type in xml_cluster.type:                    
                        type_list.append(xml_type.value.lower())
                if hasattr(xml_cluster, "super_region"):
                    for spr in xml_cluster.super_region:
                        super_region_name = spr.value.lower()
                        for region in cosmos.super_region[super_region_name]:
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
                    
                cluster_dict[name] = cl                
                
        cosmos.log("Finished reading scenario")    

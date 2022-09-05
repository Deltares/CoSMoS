# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import datetime
import os
import numpy as np
import pandas as pd
from geojson import Point, LineString, Feature, FeatureCollection
from pyproj import CRS
from pyproj import Transformer

from .cosmos_main import cosmos
from .cosmos_timeseries import merge_timeseries as merge
from .cosmos_tiling import make_wave_map_tiles
from .cosmos_tiling import make_precipitation_tiles

import cht.misc.fileops as fo
import cht.misc.misc_tools

class WebViewer:
    
    def __init__(self, name):

        self.name    = name
        self.path    = os.path.join(cosmos.config.main_path, "webviewers", name)
        self.version = cosmos.config.webviewer_version
        if fo.exists(self.path):
            self.exists = True
        else:
            self.exists = False
    
    def make(self):
        
        # Makes local copy of the web viewer
        # If such a copy already exists, data will be copied to the existing web viewer

        cosmos.log("")
        cosmos.log("Starting web viewer " + self.name +" ...")
        
        # Check whether web viewer already exists
        # If not, copy empty web viewer from templates
        if not self.exists:
            
            cosmos.log("Making new web viewer from " + self.version + " ...")

            fo.mkdir(self.path)

            template_path = os.path.join(cosmos.config.main_path,
                                         "templates",
                                         "webviewers",
                                         self.version,
                                         "*")
            fo.copy_file(template_path, self.path)

            # Change the title string in index.html to the scenario long name
            cht.misc.misc_tools.findreplace(os.path.join(self.path, "index.html"),
                                       "COSMOS_VIEWER",
                                       cosmos.scenario.long_name)

        cosmos.log("Updating scenario.js ...")

        # Check if there is a scenarios.js file
        # If so, append it with the current scenario
        sc_file = os.path.join(self.path, "data", "scenarios.js")
        update_scenarios_js(sc_file)
        
        # Make scenario folder in web viewer
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        cosmos.log("Removing old scenario folder from web viewer ...")

        fo.rmdir(scenario_path)
        fo.mkdir(os.path.join(scenario_path))
        
        # Map variables
        self.map_variables = []
  
        self.copy_timeseries()
        self.copy_floodmap()        
        self.copy_wave_maps()
        self.copy_sederomap()
        self.copy_bedlevelmaps()
        self.make_runup_map()
        self.make_meteo_maps()
        mv_file = os.path.join(scenario_path,
                               "variables.js")
        
        cht.misc.misc_tools.write_json_js(mv_file, self.map_variables, "var map_variables =")


    def copy_timeseries(self):

        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Stations and buoys
        cosmos.log("Copying time series ...")
                
        fo.mkdir(os.path.join(scenario_path, "timeseries"))
        
        # Set stations to upload (only upload for high-res nested models)
        for model in cosmos.scenario.model:
            
            all_nested_models = model.get_all_nested_models("flow")
            if all_nested_models:
                all_nested_stations = []
                for mdl in all_nested_models:
                    for st in mdl.station:
                        all_nested_stations.append(st.name)
                for station in model.station:
                    if station.type == "tide_gauge":
                        if station.name in all_nested_stations:
                            station.upload = False 
    
            all_nested_models = model.get_all_nested_models("wave")
            if all_nested_models:
                all_nested_stations = []
                for mdl in all_nested_models:
                    for st in mdl.station:
                        all_nested_stations.append(st.name)
                for station in model.station:
                    if station.type == "wave_buoy":
                        if station.name in all_nested_stations:
                            station.upload = False 
        
        # Tide stations

        features = []

        for model in cosmos.scenario.model:
            if model.station and model.flow:
                for station in model.station:
                    if station.type == "tide_gauge" and station.upload:
                        
                        point = Point((station.longitude, station.latitude))
                        name = station.long_name + " (" + station.id + ")"
                        
                        # Check if there is a file in the observations that matches this station
                        obs_file = None
                        if cosmos.scenario.observations_path and station.id:
                            obs_pth = os.path.join(cosmos.config.main_path,
                                               "observations",
                                               cosmos.scenario.observations_path,
                                               "water_levels")                        
                            fname = "waterlevel." + station.id + ".observed.csv.js"
                            if os.path.exists(os.path.join(obs_pth, fname)):
                                obs_file = fname
                                                                        
                        features.append(Feature(geometry=point,
                                                properties={"name":station.name,
                                                            "long_name":name,
                                                            "id": station.id,
                                                            "mllw":station.mllw,
                                                            "model_name":model.name,
                                                            "model_type":model.type,
                                                            "obs_file":obs_file}))
                        
                        # Merge time series from previous cycles
                        # Go two days back
                        path = cosmos.scenario.timeseries_path
#                        path = model.archive_path
                        t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
                        t1 = cosmos.cycle_time
                        v  = merge(path,
                                   model.name,
                                   model.region,
                                   model.type,
                                   station.name,
                                   t0=t0.replace(tzinfo=None),
                                   t1=t1.replace(tzinfo=None),
                                   prefix='waterlevel')
                        
                        # Check if merge returned values
                        if v is not None:                            
                            # Here we correct for NAVD88 to MSL !!!
                            v += model.vertical_reference_level_difference_with_msl                            
                            csv_file = "waterlevel." + model.name + "." + station.name + ".csv.js"
                            csv_file = os.path.join(scenario_path,
                                                    "timeseries",
                                                    csv_file)
                            s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                         float_format='%.3f',
                                         header=False)                             
                            cht.misc.misc_tools.write_csv_js(csv_file, s, 'var csv = `date_time,wl')
        
        # Save stations geojson file
        if features:
            feature_collection = FeatureCollection(features)
            stations_file = os.path.join(scenario_path,
                                    "stations.geojson.js")
            cht.misc.misc_tools.write_json_js(stations_file, feature_collection, "var stations =")
                        

        # Wave buoys
    
        features = []
    
        for model in cosmos.scenario.model:
            if model.station and model.wave:
                for station in model.station:
                    if station.type == "wave_buoy" and station.upload:                
                        point = Point((station.longitude, station.latitude))
                        if station.ndbc_id:
                            name = station.long_name + " (" + station.ndbc_id + ")"
                        else:
                            name = station.long_name
                        features.append(Feature(geometry=point,
                                                properties={"name":station.name,
                                                            "long_name":name,
                                                            "id": station.ndbc_id,
                                                            "model_name":model.name,
                                                            "model_type":model.type}))
    
                        path = cosmos.scenario.timeseries_path
                        t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
                        t1 = cosmos.cycle_time
                        
                        # Hm0
                        v  = merge(path,
                                   model.name,
                                   model.region,
                                   model.type,
                                   station.name,
                                   t0=t0.replace(tzinfo=None),
                                   t1=t1.replace(tzinfo=None),
                                   prefix='waves')
                        
                        # Check if merge returned values
                        if v is not None:                            
                            # Write csv js file
                            csv_file = "waves." + model.name + "." + station.name + ".csv.js"
                            csv_file = os.path.join(scenario_path,
                                                    "timeseries",
                                                    csv_file)
                            s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                         float_format='%.3f',
                                         header=False) 
                            cht.misc.misc_tools.write_csv_js(csv_file, s, "var csv = `date_time,hm0,tp")
    
        if features:
            feature_collection = FeatureCollection(features)
            buoys_file = os.path.join(scenario_path,
                                    "wavebuoys.geojson.js")
            cht.misc.misc_tools.write_json_js(buoys_file, feature_collection, "var buoys =")
        
        # # Extreme runup height
        # for model in cosmos.scenario.model:
        #     if model.type == 'beware':
        #         model.domain.read_data(os.path.join(model.cycle_output_path,
        #                                             "BW_output.nc"))                
        #         model.domain.write_to_geojson(scenario_path, cosmos.scenario.name)
        #         model.domain.write_to_csv(scenario_path, cosmos.scenario.name)

    def copy_floodmap(self):

        cosmos.log("Copying flood map tiles ...")

        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Flood maps
        
        # Check if flood maps are available
        flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                      "flood_map")
        
        if fo.exists(flood_map_path):
            
            # 24 hour increments  
            dtinc = 24
    
            # Wave map for the entire simulation
            dt  = datetime.timedelta(hours=dtinc)
            t0  = cosmos.cycle_time.replace(tzinfo=None)    
            t1  = cosmos.stop_time

            pathstr = []
            namestr = []
            
            # 24-hour increments
            requested_times = pd.date_range(start=t0 + dt,
                                            end=t1,
                                            freq=str(dtinc)+"H").to_pydatetime().tolist()

            for it, t in enumerate(requested_times):
                pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
                namestr.append((t - dt).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC")

            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
            td = t1 - t0
            hrstr = str(int(td.days * 24 + td.seconds/3600))
            namestr.append("Combined " + hrstr + "-hour forecast")

            wvpath = os.path.join(scenario_path)
            fo.copy_file(flood_map_path, wvpath)
            dct={}
            dct["name"]        = "flood_map"
            dct["long_name"]   = "Flood map"
            dct["description"] = "This is a flood map. It can tell if you will drown."
            dct["format"]      = "xyz_tile_layer"
            dct["max_native_zoom"]  = 13

            tms = []            
            for it, pth in enumerate(pathstr):
                tm = {}
                tm["name"]   = pth
                tm["string"] = namestr[it]
                tms.append(tm)
            dct["times"]        = tms  

            mp = next((x for x in cosmos.config.map_contours if x["name"] == "flood_map"), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []
            
            for cntr in cntrs:
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)
    
            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            self.map_variables.append(dct)

    def copy_wave_maps(self):
            
        # Wave maps
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # 24 hour increments  
        dtinc = 24

        # Wave map for the entire simulation
        dt  = datetime.timedelta(hours=dtinc)
        t0  = cosmos.cycle_time.replace(tzinfo=None)    
        t1  = cosmos.stop_time
        
        okay  = False
        for model in cosmos.scenario.model:
            if model.type=="hurrywave":
                index_path = os.path.join(model.path, "tiling", "indices")
                if model.make_wave_map and os.path.exists(index_path):            
                    okay = True

        if okay:
            
            cosmos.log("Copying wave map tiles ...")
            
            pathstr = []
            namestr = []
            
            # 6-hour increments
            requested_times = pd.date_range(start=t0 + dt,
                                            end=t1,
                                            freq=str(dtinc)+"H").to_pydatetime().tolist()

            for it, t in enumerate(requested_times):
                pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
                namestr.append((t - dt).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC")

            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
            td = t1 - t0
            hrstr = str(int(td.days * 24 + td.seconds/3600))
            namestr.append("Combined " + hrstr + "-hour forecast")
                        
            # Check if wave maps are available
            wave_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                          "hm0")
            
            wvpath = os.path.join(scenario_path)
            fo.copy_file(wave_map_path, wvpath)
            dct={}
            dct["name"]        = "hm0" 
            dct["long_name"]   = "Wave height"
            dct["description"] = "These are Hm0 wave heights."
            dct["format"]      = "xyz_tile_layer"
            dct["max_native_zoom"] = 9
            
            tms = []            
            for it, pth in enumerate(pathstr):
                tm = {}
                tm["name"]   = pth
                tm["string"] = namestr[it]
                tms.append(tm)

            dct["times"]        = tms  

            contour_set = "Hm0"    
            
            mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []                
            for cntr in cntrs:    
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)
    
            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            self.map_variables.append(dct)

                
    def copy_sederomap(self):

        cosmos.log("Copying sedimentation/erosion map tiles ...")
        
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)
             
        # Check if sedero maps are available
        sedero_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                      "sedero")
        
        if fo.exists(sedero_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(sedero_path, wvpath)
            dct={}
            dct["name"]        = "sedero"
            dct["long_name"]   = "Sedimentation/erosion"
            dct["description"] = "This is a sedimentation/erosion map. It can tell if your house will wash away."
            dct["format"]      = "xyz_tile_layer"
            dct["max_native_zoom"]  = 16

            mp = next((x for x in cosmos.config.map_contours if x["name"] == "sedero"), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []
            
            for cntr in cntrs:
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)
    
            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            self.map_variables.append(dct)


        # Markers for XBeach models that ran

        features = []
        wgs84 = CRS.from_epsg(4326)

        for model in cosmos.scenario.model:
            
            if model.type == "xbeach":
                
                # Use wave nesting point to put the marker
                xp = model.domain.wave_boundary_point[0].geometry.x
                yp = model.domain.wave_boundary_point[0].geometry.y            
                transformer = Transformer.from_crs(model.crs, wgs84, always_xy=True)
                lon, lat = transformer.transform(xp, yp)
                
                point = Point((lon, lat))
                
                features.append(Feature(geometry=point,
                                        properties={"name": model.name,
                                                    "long_name": model.long_name,
                                                    "flow_nested": model.flow_nested_name,
                                                    "wave_nested": model.wave_nested_name}))
                        
        # Save xbeach geojson file
        if features:
            feature_collection = FeatureCollection(features)
            stations_file = os.path.join(scenario_path,
                                    "xbeach.geojson.js")
            cht.misc.misc_tools.write_json_js(stations_file, feature_collection, "var xb_markers =")
            
    def make_meteo_maps(self):
        
        from cht.misc import xmlkit as xml

        cosmos.log("Making meteo map tiles ...")

        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Wind
        xml_obj = xml.xml2obj(cosmos.scenario.file_name)
        if hasattr(xml_obj, "meteo_dataset"):
            meteo_dataset = xml_obj.meteo_dataset[0].value

        for meteo_subset in cosmos.meteo_subset:
            if meteo_dataset == meteo_subset.name:
                
                # TODO these ranges 
                xlim = [-99.0, -55.0]
                ylim = [8.0, 45.0]
                
                if meteo_subset.x is not None:
                    
                    subset = meteo_subset.subset(xlim=xlim,
                                                 ylim=ylim,
                                                 time_range=[],
                                                 stride=2)
                    # Get maximum wind speed
                    u = subset.quantity[0].u
                    v = subset.quantity[0].v
                    vmag = np.sqrt(u*u + v*v)
                    wndmx = np.max(vmag)
                    
                    file_name = os.path.join(scenario_path, "wind.json.js")
                    subset.write_wind_to_json(file_name, time_range=None, js=True)
                    
                    # Add wind to map variables
    
                    if wndmx<=20.0:
                        contour_set = "wnd20"
                        wndmx=20.0                
                    elif wndmx<=40.0:   
                        contour_set = "wnd40"
                        wndmx=40.0                
                    else:   
                        contour_set = "wnd60"
                        wndmx=60.0                
            
                    dct={}
                    dct["name"]        = "wind"
                    dct["long_name"]   = "Wind"
                    dct["description"] = "This is a wind map. It can tell if your house will blow away."
                    dct["format"]      = "vector_field"
                    dct["max"]         = wndmx
        
                    mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)    
                    
                    lgn = {}
                    lgn["text"] = mp["string"]
                        
                    cntrs = mp["contours"]
        
                    contours = []
                    
                    for cntr in cntrs:    
                        contour = {}
                        contour["text"]  = cntr["string"]
                        contour["color"] = "#" + cntr["hex"]
                        contours.append(contour)
            
                    lgn["contours"] = contours
                    dct["legend"]   = lgn
                    
                    self.map_variables.append(dct)
                    
                    # Cyclone track(s)
                    subset = meteo_subset.subset(time_range=[],
                                                 stride=1)
    
                    tracks = meteo_subset.find_cyclone_tracks(xlim=[-110.0,-30.0],
                                                              ylim=[5.0, 45.0],
                                                              pcyc=99500.0)
                    
                    if tracks:
                        features = []
                        for track in tracks:
                            
                            points=[]
                        
                            for ip in range(np.size(track.lon)):
                                point = Point((track.lon[ip], track.lat[ip]))               
                                if track.vmax[ip]<64.0:
                                    cat = "TS"
                                elif track.vmax[ip]<83.0:
                                    cat = "1"
                                elif track.vmax[ip]<96.0:    
                                    cat = "2"
                                elif track.vmax[ip]<113.0:    
                                    cat = "3"
                                elif track.vmax[ip]<137.0:    
                                    cat = "4"
                                else:    
                                    cat = "5"
                                features.append(Feature(geometry=point,
                                                        properties={"time":track.time[ip].strftime("%Y/%m/%d %H:%M") + " UTC",
                                                                    "lon":track.lon[ip],
                                                                    "lat":track.lat[ip],
                                                                    "vmax":1.13*track.vmax[ip]/1.94384,
                                                                    "pc":track.pc[ip],
                                                                    "category":cat}))
                                
                                points.append([track.lon[ip], track.lat[ip]])
                            
                            trk = LineString(coordinates=points)
                            features.append(Feature(geometry=trk,
                                                    properties={"name":"No name"}))
                        
                        feature_collection = FeatureCollection(features)
                        file_name = os.path.join(scenario_path, "track.geojson.js")
                        cht.misc.misc_tools.write_json_js(file_name,
                                                          feature_collection,
                                                          "var track_data =")
                                
        
        # Cumulative rainfall
        
        # Rainfall map for the entire simulation
        dt1 = datetime.timedelta(hours=1)
#        dt6 = datetime.timedelta(hours=6)
        dt24 = datetime.timedelta(hours=24)
        t0 = cosmos.cycle_time.replace(tzinfo=None)    
        t1 = cosmos.stop_time
        
        # First determine max precip for all simulations 
        pmx = 0.0
        okay  = False
        for model in cosmos.scenario.model:
            if model.type=="sfincs":
                index_path = os.path.join(model.path, "tiling", "indices")
#                if model.make_precip_map and os.path.exists(index_path):            
                if os.path.exists(index_path):            
                    file_name = os.path.join(model.cycle_output_path, "sfincs_map.nc")
                    # p0max = model.domain.read_cumulative_precipitation(file_name=file_name,
                    #                                                    time_range=[t0 + dt1, t1 + dt1])
                    # pmx = max(pmx, np.nanmax(p0max))
                    okay = True

        if okay:

            cosmos.log("Making precipitation tiles ...")                
                
            print("Maximum precipitation : " + '%6.2f'%pmx + " mm")                         

            contour_set = "precip_log"    

            pathstr = []
            namestr = []
            
            # 24-hour increments
            requested_times = pd.date_range(start=t0 + dt24,
                                            end=t1,
                                            freq='24H').to_pydatetime().tolist()

            for it, t in enumerate(requested_times):
                pathstr.append((t - dt24).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
                namestr.append((t - dt24).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC")

            for model in cosmos.scenario.model:
                if model.type=="sfincs":
                    index_path = os.path.join(model.path, "tiling", "indices")            
#                    if model.make_wave_map and os.path.exists(index_path):                            
                    if os.path.exists(index_path):                            
                        
                        cosmos.log("Making precip tiles for model " + model.long_name + " ...")                
    
                        file_name = os.path.join(model.cycle_output_path, "sfincs_map.nc")
                        
                        # Precip map over 24-hour increments                    
                        for it, t in enumerate(requested_times):
                            p = model.domain.read_cumulative_precipitation(file_name=file_name,
                                                                           time_range=[t - dt24 + dt1, t + dt1])                        
                            p_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                        "precipitation",
                                                        pathstr[it])                        
                            make_precipitation_tiles(p, index_path, p_map_path, contour_set)
    
                        # # Full simulation        
                        # hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                        #                             "hm0",
                        #                             pathstr[-1])                    
                        # hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                        #                                   time_range=[t0, t1 + dt1])        
                        # make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)
            
            # Check if wave maps are available
            p_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                          "precipitation")
            
            ppath = os.path.join(scenario_path)
            fo.copy_file(p_map_path, ppath)
            dct={}
            dct["name"]        = "precipitation" 
            dct["long_name"]   = "Cumulative rainfall"
            dct["description"] = "These are cumulative precipitations."
            dct["format"]      = "xyz_tile_layer"
            dct["max_native_zoom"]  = 10
            
            tms = []            
            for it, pth in enumerate(pathstr):
                tm = {}
                tm["name"]   = pth
                tm["string"] = namestr[it]
                tms.append(tm)

            dct["times"]        = tms  
            
            mp = next((x for x in cosmos.config.map_contours if x["name"] == contour_set), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []
            
            for cntr in cntrs:
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)
    
            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            self.map_variables.append(dct)

    def copy_bedlevelmaps(self):

        cosmos.log("Copying bed level map tiles ...")
        
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)
             
        # Check if sedero maps are available
        zb0_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                      "zb0")
        zbend_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                              "zbend")
        
        if fo.exists(zb0_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(zb0_path, wvpath)
            dct={}
            dct["name"]        = "zb0"
            dct["long_name"]   = "Pre-storm bed level"
            dct["description"] = "These were the bed levels prior to the storm"
            dct["format"]      = "xyz_tile_layer"

            mp = next((x for x in cosmos.config.map_contours if x["name"] == "bed_levels"), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []

            for cntr in cntrs:
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)    
            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            # for icntr,cntr in enumerate(cntrs):
            #     if icntr in np.arange(0, 101,10):
            #         contour = {}
            #         contour["text"]  = cntr["string"]
            #         contour["color"] = "#" + cntr["hex"]
            #         contours.append(contour)
        
            #         lgn["contours"] = contours
            #         dct["legend"]   = lgn
            #     else:
            #         continue
            
            self.map_variables.append(dct)
            
        if fo.exists(zbend_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(zbend_path, wvpath)
            dct={}
            dct["name"]        = "zbend"
            dct["long_name"]   = "Post-storm bed level"
            dct["description"] = "These are the predicted bed levels after the storm"
            dct["format"]      = "xyz_tile_layer"

            mp = next((x for x in cosmos.config.map_contours if x["name"] == "bed_levels"), None)    
            
            lgn = {}
            lgn["text"] = mp["string"]

            cntrs = mp["contours"]

            contours = []
            
            for cntr in cntrs:
                contour = {}
                contour["text"]  = cntr["string"]
                contour["color"] = "#" + cntr["hex"]
                contours.append(contour)    
            lgn["contours"] = contours
            dct["legend"]   = lgn


            # cntrs = mp["contours"]

            # contours = []
            
            # for icntr,cntr in enumerate(cntrs):
            #     if icntr in np.arange(0, 101,10):
            #         contour = {}
            #         contour["text"]  = cntr["string"]
            #         contour["color"] = "#" + cntr["hex"]
            #         contours.append(contour)
        
            #         lgn["contours"] = contours
            #         dct["legend"]   = lgn
            #     else:
            #         continue
            
            self.map_variables.append(dct)
            

    def make_runup_map(self):        

        output_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Extreme runup height

        for model in cosmos.scenario.model:
            if model.type == 'beware':

                

                model.domain.read_data(os.path.join(model.cycle_output_path,
                                                    "BW_output.nc"))                

                features = []
                transformer = Transformer.from_crs(model.crs,
                                                   'WGS 84',
                                                   always_xy=True)
                
                for ip in range(len(model.domain.filename)):
                    x, y = transformer.transform(model.domain.xp[ip],
                                                 model.domain.yp[ip])
                    point = Point((x, y))
                    name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                
                    id = np.argmax(model.domain.R2p[ip,:])                                                                       
                    features.append(Feature(geometry=point,
                                            properties={"model_name":model.name,
                                                        "LocNr":int(model.domain.filename[ip]),
                                                        "Lon":x,
                                                        "Lat":y,                                                
                                                        "Setup":round(model.domain.setup[ip, id],2),
                                                        "Swash":round(model.domain.swash[ip, id],2),
                                                        "TWL":round(model.domain.R2p[ip, id],2)}))
                
                feature_collection = FeatureCollection(features)
                
                if features:
                    feature_collection = FeatureCollection(features)
                    output_path_runup =  os.path.join(output_path, 'extreme_runup_height\\')
                    fo.mkdir(output_path_runup)
                    file_name = os.path.join(output_path_runup,
                                            "extreme_runup_height.geojson.js")
                    cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var runup =")

                dct={}
                dct["name"]        = "extreme_runup_height"
                dct["long_name"]   = "Extreme run-up"
                dct["description"] = "These are the predicted extreme run-up heights"
                dct["format"]      = "geojson"


                mp = next((x for x in cosmos.config.map_contours if x["name"] == "run_up"), None)                    
 
                lgn = {}
                lgn["text"] = mp["string"]
    
                cntrs = mp["contours"]
    
                contours = []
                
                for cntr in cntrs:
                    contour = {}
                    contour["text"]  = cntr["string"]
                    contour["color"] = "#" + cntr["hex"]
                    contours.append(contour)
        
                lgn["contours"] = contours
                dct["legend"]   = lgn

    
                self.map_variables.append(dct)

                    
                # features = []
                    
                # for ip in range(len(model.domain.filename)):
                #     x, y = transformer.transform(model.domain.xo[ip],
                #                                   model.domain.yo[ip])
                #     point = Point((x, y))
                #     name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                
                #     id = np.argmax(model.domain.R2p[ip,:])                                                                       
                #     features.append(Feature(geometry=point,
                #                             properties={"LocNr":int(model.domain.filename[ip]),
                #                                         "Lon": x,
                #                                         "Lat": y,
                #                                         "Hs":round(model.domain.Hs[ip, id],2),
                #                                         "Tp":round(model.domain.Tp[ip, id],1),
                #                                         "WL":round(model.domain.WL[ip, id],2)}))
                
                # feature_collection = FeatureCollection(features)
                
                # if features:
                #     feature_collection = FeatureCollection(features)
                #     output_path_waves =  os.path.join(output_path, 'extreme_sea_level_and_wave_height\\')
                #     os.mkdir(output_path_waves)
                #     file_name = os.path.join(output_path_waves,     
                #                             "extreme_sea_level_and_wave_height.geojson.js")
                #     cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var swl =")
                # # with open(output_path + r"\\" + scenario + '.TWL.geojson.js', 'w') as fl:
                # #     fl.write('const point_' + scenario + '_TWL = ')
                # #     dump(feature_collection, fl)
                # #     fl.write("  \n   \n")
                # #     fl.write('pt_' + scenario + '_' + 'BT' + '_TWL.addData(point_' + scenario + '_TWL);')

                # dct={}
                # dct["name"]        = "extreme_sea_level_and_wave_height"
                # dct["long_name"]   = "Extreme run-up boundaries"
                # dct["description"] = "These are the run-up boundary conditions"
                # dct["format"]      = "geojson"

                # mp = next((x for x in cosmos.config.map_contours if x["name"] == "run_up"), None)                    
 
                # lgn = {}
                # lgn["text"] = mp["string"]
    
                # cntrs = mp["contours"]
    
                # contours = []
                
                # for cntr in cntrs:
                #     contour = {}
                #     contour["text"]  = cntr["string"]
                #     contour["color"] = "#" + cntr["hex"]
                #     contours.append(contour)
        
                # lgn["contours"] = contours
                # dct["legend"]   = lgn
    
                # self.map_variables.append(dct)


        # Time series 
            
        for ip in range(len(model.domain.filename)):

            d= {'WL': model.domain.WL[ip,:],'Setup': model.domain.setup[ip,:], 'Swash': model.domain.swash[ip,:], 'Runup': model.domain.R2p[ip,:]}       

            v= pd.DataFrame(data=d, index =  pd.date_range(model.domain.input.tstart, periods=len(model.domain.swash[ip,:]), freq= '0.5H'))
            obs_file = "extreme_runup_height." + model.domain.runid + "." +str(model.domain.filename[ip]) + ".csv.js"

            local_file_path = os.path.join(output_path,  "timeseries",
                                               obs_file)
#            local_file_path = os.path.join(output_path,  
#                                           obs_file)
            s= v.to_csv(path_or_buf=None,
                         date_format='%Y-%m-%dT%H:%M:%S',
                         float_format='%.3f',
                         header= False, index_label= 'datetime')        
            
            cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup")


#         features = []
            
#         for ip in range(len(self.filename)):
#             x, y = transformer.transform(self.xp[ip],
#                                          self.yp[ip])
#             point = Point((x, y))
#             name = 'Loc nr: ' +  str(self.filename[ip])
                        
#             obs_file = "extreme_runup_height." + self.runid + "." +str(self.filename[ip]) + ".csv.js"
                                                          
#             features.append(Feature(geometry=point,
#                                     properties={"name":int(self.filename[ip]),
#                                                 "LocNr":int(self.filename[ip]),
#                                                 "Lon":x,
#                                                 "Lat":y,
#                                                 "model_name":self.name,
#                                                 "model_type":self.type,
#                                                 "TWL":  np.round(np.max(self.R2p[ip,:]),2),
#                                                 "obs_file": obs_file}))
#             d= {'WL': self.WL[ip,:],'Setup': self.setup[ip,:], 'Swash': self.swash[ip,:], 'Runup': self.R2p[ip,:]}       
#             v= pd.DataFrame(data=d, index =  pd.date_range(self.input.tstart, periods=len(self.swash[ip,:]), freq= '0.5H'))
    
#             local_file_path = os.path.join(output_path,  "timeseries",
#                                                obs_file)
# #            local_file_path = os.path.join(output_path,  
# #                                           obs_file)
#             s= v.to_csv(path_or_buf=None,
#                          date_format='%Y-%m-%dT%H:%M:%S',
#                          float_format='%.3f',
#                          header= False, index_label= 'datetime')        
            
#             cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup")
                             
#         if features:
#             feature_collection = FeatureCollection(features)
#             runup_file = os.path.join(output_path,
#                                     "twls.geojson.js")
#             cht.misc.misc_tools.write_json_js(runup_file, feature_collection, "var TWL =")




#                model.domain.write_to_geojson(scenario_path, cosmos.scenario.name)
#                model.domain.write_to_csv(scenario_path, cosmos.scenario.name)


    def upload(self):        

        from cht.misc.sftp import SSHSession
        
        cosmos.log("Uploading web viewer ...")
        
        # Upload entire copy of local web viewer to web server
        
        try:
            f = SSHSession(cosmos.config.ftp_hostname,
                           username=cosmos.config.ftp_username,
                           password=cosmos.config.ftp_password)
        except:
            cosmos.log("Error! Could not connect to sftp server !")
            return
        
        try:
            
            # Check if web viewer already exist
            make_wv_on_ftp = False
            if not self.exists:
                # Web viewer does not even exist locally
                make_wv_on_ftp = True
            else:
                # Check if web viewer exists on FTP
                if not self.name in f.sftp.listdir(cosmos.config.ftp_path):
                    make_wv_on_ftp = True
                    
            if make_wv_on_ftp:
                # Copy entire webviewer
                f.put_all(self.path, cosmos.config.ftp_path)
    
            else:
                # Webviewer already on ftp server
                
                # Only copy scenario output
                scenario_path = os.path.join(self.path,
                                             "data",
                                             cosmos.scenario.name)
                remote_path = cosmos.config.ftp_path + "/" + self.name + "/data"
                # Check if scenario is already on ftp server
                cosmos.log("Removing existing data on web server ...")
                if cosmos.scenario.name in f.sftp.listdir(remote_path):
                    f.rmtree(remote_path + "/" + cosmos.scenario.name)
                    
                # Copy scenarios.js    
                remote_file = remote_path + "/scenarios.js"
                local_file  = os.path.join(".", "scenarios.js")
                f.get(remote_file, local_file)
                update_scenarios_js(local_file)                
                # Copy new scenarios.js to server
                f.put(local_file, remote_path + "/scenarios.js")
                # Delete local scenarios.js
                fo.rm(local_file)

                # Copy scenario data to server
                cosmos.log("Uploading all data to web server ...")
                f.put_all(scenario_path, remote_path)
            
            f.sftp.close()    
    
            cosmos.log("Done uploading.")
            
        except BaseException as e:
            cosmos.log("An error occurred while uploading !")
            cosmos.log(str(e))
            
            try:
                f.sftp.close()    
            except:
                pass


    def upload_data(self):        
        # Upload data from local web viewer to web server
        pass

def update_scenarios_js(sc_file):
    
    # Check if there is a scenarios.js file
    # If so, append it with the current scenario
    isame = -1
    cosmos.log("Updating scenario file : " + sc_file)
    if fo.exists(sc_file):
        scs = cht.misc.misc_tools.read_json_js(sc_file)
        for isc, sc in enumerate(scs):
            if sc["name"] == cosmos.scenario.name:
                isame = isc
    else:
        scs = []

    # Current scenario        
    newsc = {}
    newsc["name"]        = cosmos.scenario.name    
    newsc["long_name"]   = cosmos.scenario.long_name    
    newsc["description"] = cosmos.scenario.description    
    newsc["lon"]         = cosmos.scenario.lon    
    newsc["lat"]         = cosmos.scenario.lat
    newsc["zoom"]        = cosmos.scenario.zoom    
    newsc["cycle"]       = cosmos.cycle_time.strftime('%Y-%m-%dT%H:%M:%S')
    newsc["duration"]    = str(cosmos.scenario.run_duration)

    now = datetime.datetime.utcnow()
    newsc["last_update"] = now.strftime("%Y/%m/%d %H:%M:%S" + " (UTC)")

    if isame>-1:
        # Scenario already existed in web viewer
        scs[isame] = newsc
    else:
        # New scenario in web viewer    
        scs.append(newsc)        

    cht.misc.misc_tools.write_json_js(sc_file, scs, "var scenario =")

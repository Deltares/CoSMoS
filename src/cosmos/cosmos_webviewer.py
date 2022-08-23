# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import datetime
import os
import numpy as np
import pandas as pd
from geojson import Point, Feature, FeatureCollection
from pyproj import CRS
from pyproj import Transformer

from .cosmos_main import cosmos
from .cosmos_timeseries import merge_timeseries as merge
from .cosmos_tiling import make_wave_map_tiles

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
            cht.misc_tools.findreplace(os.path.join(self.path, "index.html"),
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
        fo.rmdir(scenario_path)
        fo.mkdir(os.path.join(scenario_path))
        
        # Map variables
        self.map_variables = []
  
        self.copy_timeseries()
        self.copy_floodmap()        
        self.make_wave_maps()
        self.copy_sederomap()
#        self.make_meteo_maps()

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
        
        # Extreme runup height
        for model in cosmos.scenario.model:
            if model.type == 'beware':
                model.domain.read_data(os.path.join(model.cycle_output_path,
                                                    "BW_output.nc"))                
                model.domain.write_to_geojson(scenario_path, cosmos.scenario.name)
                model.domain.write_to_csv(scenario_path, cosmos.scenario.name)

    def copy_floodmap(self):

        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)
             
        
        # Flood maps
        
        # Check if flood maps are available
        flood_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                      "flood_map")
        
        if fo.exists(flood_map_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(flood_map_path, wvpath)
            dct={}
            dct["name"]        = "flood_map"
            dct["long_name"]   = "Flood map"
            dct["description"] = "This is a flood map. It can tell if you will drown."
            dct["format"]      = "xyz_tile_layer"

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

    def make_wave_maps(self):
            
        # Wave maps
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Make wave map tiles
        if cosmos.config.make_wave_maps:

            # Wave map for the entire simulation
            dt1 = datetime.timedelta(hours=1)
            dt6 = datetime.timedelta(hours=6)
#            dt7 = datetime.timedelta(hours=7)
            t0 = cosmos.cycle_time.replace(tzinfo=None)    
            t1 = cosmos.stop_time
            
            # First determine max wave height for all simulations 
            hm0mx = 0.0
            okay  = False
            for model in cosmos.scenario.model:
                if model.type=="hurrywave":
                    index_path = os.path.join(model.path, "tiling", "indices")
                    if model.make_wave_map and os.path.exists(index_path):            
                        file_name = os.path.join(model.cycle_output_path, "hurrywave_map.nc")
                        hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                                                          time_range=[t0, t1 + dt1])
                        hm0mx = max(hm0mx, np.nanmax(hm0max))
                        okay = True

            if okay:
                cosmos.log("Making wave map tiles ...")                
                    
                print("Maximum wave height : " + '%6.2f'%hm0mx + " m")                         
    
                # Set color scale
                if hm0mx<=2.0:
                    contour_set = "Hm0_2m"
                elif hm0mx<=5.0:   
                    contour_set = "Hm0_5m"
                elif hm0mx<=10.0:   
                    contour_set = "Hm0_10m"
                elif hm0mx<=20.0:   
                    contour_set = "Hm0_20m"
    
    
                pathstr = []
                namestr = []
                
                # 6-hour increments
                requested_times = pd.date_range(start=t0 + dt6,
                                                end=t1,
                                                freq='6H').to_pydatetime().tolist()
    
                for it, t in enumerate(requested_times):
                    pathstr.append((t - dt6).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
                    namestr.append((t - dt6).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC")
    
                pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))
                td = t1 - t0
                hrstr = str(int(td.days * 24 + td.seconds/3600))
                namestr.append("Combined " + hrstr + "-hour forecast")
                    
                for model in cosmos.scenario.model:
                    if model.type=="hurrywave":
                        index_path = os.path.join(model.path, "tiling", "indices")            
                        if model.make_wave_map and os.path.exists(index_path):                            
                            
                            cosmos.log("Making wave map tiles for model " + model.long_name + " ...")                
        
                            file_name = os.path.join(model.cycle_output_path, "hurrywave_map.nc")
                            
                            # Wave map over 6-hour increments                    
                            for it, t in enumerate(requested_times):
                                hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                                                                  time_range=[t - dt1, t + dt1])                        
                                hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                            "hm0",
                                                            pathstr[it])                        
                                make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)
        
                            # Full simulation        
                            hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                        "hm0",
                                                        pathstr[-1])                    
                            hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                                                              time_range=[t0, t1 + dt1])        
                            make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)
                
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
                
    def copy_sederomap(self):

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
                xp = model.wave_nesting_point_x[0]
                yp = model.wave_nesting_point_y[0]                
                transformer = Transformer.from_crs(model.crs, wgs84, always_xy=True)
                lon, lat = transformer.transform(xp, yp)
                
                point = Point((lon, lat))
                
                features.append(Feature(geometry=point,
                                        properties={"name": model.name,
                                                    "long_name": model.long_name}))
                        
        # Save xbeach geojson file
        if features:
            feature_collection = FeatureCollection(features)
            stations_file = os.path.join(scenario_path,
                                    "xbeach.geojson.js")
            cht.misc.misc_tools.write_json_js(stations_file, feature_collection, "var xb_markers =")
            
    def make_meteo_maps(self):
        
        from cht.misc import xmlkit as xml

        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)

        # Wind
        xml_obj = xml.xml2obj(cosmos.scenario.file_name)
        if hasattr(xml_obj, "meteo_dataset"):
            meteo_dataset = xml_obj.meteo_dataset[0].value

        for meteo_subset in cosmos.meteo_subset:
            if meteo_dataset == meteo_subset.name:
                file_name = os.path.join(scenario_path, "wind.json")
                meteo_subset.write_wind_to_json(file_name, time_range=None, iref=2, js=True)
                
                # Add wind to map variables

                wndmx=25.0
    
                if wndmx<=20.0:
                    contour_set = "wnd20"
                elif wndmx<=40.0:   
                    contour_set = "wnd40"
                else:   
                    contour_set = "wnd60"
        
                dct={}
                dct["name"]        = "wind"
                dct["long_name"]   = "Wind"
                dct["description"] = "This is a wind map. It can tell if your house will blow away."
                dct["format"]      = "vector_field"
    
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
        
        # Cumulative rainfall



        pass

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

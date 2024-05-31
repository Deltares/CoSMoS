# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import datetime
import os
import shutil
import numpy as np
import pandas as pd
from scipy import interpolate                
from geojson import Point, LineString, Feature, FeatureCollection
from pyproj import CRS
from pyproj import Transformer
import boto3

from .cosmos_main import cosmos

import cht.misc.fileops as fo
import cht.misc.misc_tools

class WebViewer:
    """Cosmos webviewer class
    """    

    def __init__(self, name):
        """Initialize webviewer. 
        - Makes local copy of the webviewer from a template. If such a copy already exists, data will be copied to the existing webviewer.
        - Updating the scenario.js with the current scenario.
        - Make a variable file defining the variables that are mapped for the current scenario.

        Parameters
        ----------
        name : str
            Name of webviewer.
        """
        self.name    = name
        self.path    = os.path.join(cosmos.config.path.main, "webviewers", name)
        self.version = cosmos.config.webviewer.version
        if fo.exists(self.path):
            self.exists = True
        else:
            self.exists = False
        
        # Check whether web viewer already exists
        # If not, copy empty web viewer from templates
        if not self.exists:
            
            cosmos.log("Making new web viewer from " + self.version + " ...")

            fo.mkdir(self.path)

            template_path = os.path.join(cosmos.config.path.main,
                                         "configuration",
                                         "webviewer_templates",
                                         self.version,
                                         "*")
            fo.copy_file(template_path, self.path)

            # Change the title string in index.html to the scenario long name
            cht.misc.misc_tools.findreplace(os.path.join(self.path, "index.html"),
                                            "COSMOS_VIEWER",
                                            cosmos.scenario.long_name)

    

    def make(self):

        cosmos.log("Updating scenario.js ...")

        # Update scenario.js
        self.update_scenarios_js()
        
        # Make scenario folder in web viewer
        self.cycle_path = os.path.join(self.path,
                                       "data",
                                       cosmos.scenario.name,
                                       cosmos.cycle_string)

        # Make scenario folder and cycle folder 
        cosmos.log("Making new cycle folder on web viewer ...")
        fo.mkdir(os.path.join(self.path, "data", cosmos.scenario.name))
        fo.mkdir(os.path.join(self.path, "data", cosmos.scenario.name, cosmos.cycle_string))

#        # In cloud mode, also make a path on S3
#        if cosmos.config.cycle.run_mode == "cloud":

        # Stations and buoys
        cosmos.log("Copying time series ...")                
        fo.mkdir(os.path.join(self.cycle_path, "timeseries"))        
        # Set stations to upload (only upload for high-res nested models)
        for model in cosmos.scenario.model:
            model.set_stations_to_upload()
        self.make_timeseries("wl")
        self.make_timeseries("waves")

        # Map tiles
        cosmos.log("Adding tile layers ...")                
        self.map_variables = []

        if cosmos.config.cycle.make_flood_maps:
            self.set_map_tile_variables("flood_map",
                                        "Flood map",
                                        "This is a flood map. It can tell if you will drown.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["flood_map"]["color_map"]],
                                        13)
            self.set_map_tile_variables("flood_map_90",
                                        "Flood map (90)",
                                        "This is a worst case flood map. It can tell if you will drown.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["flood_map"]["color_map"]],
                                        13)
            
        if cosmos.config.cycle.make_wave_maps:
            self.set_map_tile_variables("hm0",
                                        "Wave height",
                                        "These are Hm0 wave heights.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["hm0"]["color_map"]],
                                        9)
            
            self.set_map_tile_variables("hm0_90",
                                        "Wave height (90)",
                                        "These are worst case Hm0 wave heights.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["hm0"]["color_map"]],
                                        9)
        
        if cosmos.config.cycle.make_water_level_maps:
            self.set_map_tile_variables("water_level",
                                        "Peak water level",
                                        "These were the peak water levels during the storm.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["water_level_map"]["color_map"]],
                                        13)
            self.set_map_tile_variables("water_level_90",
                                        "Peak water level (90)",
                                        "These were the worst-case peak water levels during the storm.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["water_level_map"]["color_map"]],
                                        13)

        if cosmos.config.cycle.make_meteo_maps:
            self.set_map_tile_variables("precipitation",
                                        "Cumulative rainfall",
                                        "These are cumulative precipitations.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["precipitation"]["color_map"]],
                                        10)
            cosmos.log("Adding meteo layers ...")                
            self.make_meteo_maps()

        if cosmos.config.cycle.make_sedero_maps:
            self.set_map_tile_variables("sedero",
                            "Sedimentation/erosion",
                            "This is a sedimentation/erosion map. It can tell if your house will wash away.",
                            cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["sedero"]["color_map"]],
                            16)
            self.set_map_tile_variables("zb0",
                                        "Pre-storm bed level",
                                        "These were the bed levels prior to the storm.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["bed_levels"]["color_map"]],
                                        16)
            self.set_map_tile_variables("zbend",
                                        "Post-storm bed level",
                                        "These were the bed levels after the storm.",
                                        cosmos.config.map_contours[cosmos.config.webviewer.tile_layer["bed_levels"]["color_map"]],
                                        16)
            cosmos.log("Adding run-up layers ...")                
            self.make_runup_map()
            cosmos.log("Adding XBeach markers ...")                
            self.make_xb_markers()
            cosmos.log("Adding XBeach regimes ...")                
            self.make_xb_regimes()

        # Write map variables to file
        cosmos.log("Writing variables ...")                
        mv_file = os.path.join(self.cycle_path, "variables.js")        
        cht.misc.misc_tools.write_json_js(mv_file, self.map_variables, "var map_variables =")

        cosmos.log("Web viewer done.")                

    def set_map_tile_variables(self, name, long_name, description, color_map, max_native_zoom):

        folders = [] 
        # Check if tiles are available
        if cosmos.config.cycle.run_mode == "cloud":
            bucket_name = 'scenario-webviewer'
            prefix = self.name + "/data/" + cosmos.scenario.name + "/" + cosmos.cycle_string + "/" + name
            folders = cosmos.cloud.list_folders(bucket_name, prefix)
        else:    
            # Tiles are stored locally
            tile_path = os.path.join(self.cycle_path, name)
            if fo.exists(tile_path):
                # Check times
                folders = fo.list_folders(os.path.join(tile_path, "*"), basename=True)

        if not folders:
            return
        
        # Get labels for the maps in the webviewer based on the folder names
        t0  = cosmos.cycle.replace(tzinfo=None)    
        t1  = cosmos.stop_time
        td = t1 - t0
        
        pathstr = []
        namestr = []
        hrstr = str(int(td.days * 24 + td.seconds/3600))

        for folder in folders:
            pathstr.append(folder)
            if folder[0:3] == "com":
                namestr.append("Combined " + hrstr + "-hour forecast")
            else:
                # Define the format of the original string
                format_str = "%Y%m%d_%HZ"

                # Extract the start and end date-time substrings
                start_str = folder[:12]  # First 12 characters, e.g.: '20240503_12Z'
                end_str = folder[13:]    # From the 14th character to the end, e.g.: '20240504_12Z'

                # Parse the start and end times
                start_time = datetime.strptime(start_str, format_str)
                end_time = datetime.strptime(end_str, format_str)

                # Define the new format for the output
                output_format = "%Y-%m-%d %H:%M"

                # Convert to the new format
                start_nice = start_time.strftime(output_format)
                end_nice = end_time.strftime(output_format)

                namestr.append(start_nice + " - " + end_nice + " UTC")

        # Add to map variables
        dct={}
        dct["name"]        = name
        dct["long_name"]   = long_name
        dct["description"] = description
        dct["format"]      = "xyz_tile_layer"
        dct["max_native_zoom"]  = max_native_zoom

        tms = []            
        for it, pth in enumerate(pathstr):
            tm = {}
            tm["name"]   = pth
            tm["string"] = namestr[it]
            tms.append(tm)
        dct["times"]        = tms  

        dct["legend"] = make_legend(mp = color_map)

        self.map_variables.append(dct)
                
    def make_xb_markers(self):
        """Make geojson file with markers for XBeach models that ran."""
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
            stations_file = os.path.join(self.cycle_path,
                                    "xbeach.geojson.js")
            cht.misc.misc_tools.write_json_js(stations_file, feature_collection, "var xb_markers =")
            
    def make_meteo_maps(self):
        
        cosmos.log("Making meteo map tiles ...")

        try:
            # Wind
            meteo_dataset = cosmos.scenario.meteo_dataset

            for meteo_subset in cosmos.meteo_subset:
                if meteo_dataset == meteo_subset.name:
                    
                    # TODO these ranges should be in the config file
                    xlim = [-99.0, -55.0]
                    ylim = [8.0, 45.0]
                                                        
                    subset = meteo_subset.subset(xlim=xlim,
                                                 ylim=ylim,
                                                 time_range=[],
                                                 stride=2)
                    # Get maximum wind speed
                    u = subset.quantity[0].u
                    v = subset.quantity[0].v
                    vmag = np.sqrt(u*u + v*v)
                    wndmx = np.max(vmag)
                    
                    file_name = os.path.join(self.cycle_path, "wind.json.js")
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
                    mp = cosmos.config.map_contours[contour_set]                    
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
                    # TODO: move a lot of this code to cht_cyclones
                    tracks = meteo_subset.find_cyclone_tracks(xlim=[-110.0,-30.0],
                                                              ylim=[5.0, 45.0],
                                                              pcyc=99500.0,
                                                              dt=6)
                    
                    if tracks:
                        features = []
                        for track in tracks:                            
                            points=[]
                            # Loop through items in geodataframe
                            for index, row in track.track.iterrows():
                                time = row['datetime']
                                lon = row['geometry'].x
                                lat = row['geometry'].y
                                vmax = row['vmax']
                                pc = row['pc']
                                point = Point((lon, lat))               
                                if vmax<64.0:
                                    cat = "TS"
                                elif vmax<83.0:
                                    cat = "1"
                                elif vmax<96.0:    
                                    cat = "2"
                                elif vmax<113.0:    
                                    cat = "3"
                                elif vmax<137.0:    
                                    cat = "4"
                                else:    
                                    cat = "5"
                                features.append(Feature(geometry=point,
                                                        properties={"time":time + " UTC",
                                                                    "lon":lon,
                                                                    "lat":lat,
                                                                    "vmax":vmax,
                                                                    "pc":pc,
                                                                    "category":cat}))
                                
                                points.append([lon, lat])
                            
                            trk = LineString(coordinates=points)
                            features.append(Feature(geometry=trk,
                                                    properties={"name":"No name"}))
                        
                        feature_collection = FeatureCollection(features)

                        file_name = os.path.join(self.cycle_path, "track.geojson.js")
                        cht.misc.misc_tools.write_json_js(file_name,
                                                          feature_collection,
                                                          "var track_data =")
        except Exception as e:
            print(str(e))

        if cosmos.scenario.track_ensemble:
            try:
                feature_collection = cosmos.scenario.track_ensemble.get_feature_collection()
                file_name = os.path.join(self.cycle_path, "track_ensemble.geojson.js")
                cht.misc.misc_tools.write_json_js(file_name,
                                                feature_collection,
                                                "var track_ensemble_data =")
            except Exception as e:
                print(str(e))



    def make_xb_regimes(self):        
        """Make Sallenger regimes markers for webviewer.
        """   
        output_path = self.cycle_path
        df_all = pd.DataFrame()

        # Sallenger regimes

        for model in cosmos.scenario.model:
            if model.type == 'xbeach':

                #if os.path.exists(os.path.join(model.cycle_output_path,
                 #                           "beware_his.nc")) and not model.ensemble:

                 # Check if Sallenger regimes are calculated

                if os.path.exists(os.path.join(model.cycle_post_path,"Sallengerregimes.csv")):

                                    
                    csv_file = os.path.join(model.cycle_post_path,"Sallengerregimes.csv")
                    df = pd.read_csv(csv_file)
                    
                    transformer = Transformer.from_crs(model.crs,
                                                            'WGS 84',
                                                            always_xy=True)
                    
                    df_all = pd.concat([df_all, df], ignore_index= True)

           
        features = []    
        for ip in range(len(df_all)):
            lon, lat = transformer.transform(df_all.X[ip],df_all.Y[ip])
            point = Point((lon, lat))
                        
            features.append(Feature(geometry=point,
            properties={"LocNr":int(ip),
                        "Lon":lon,
                        "Lat":lat,                                                
                        "regime":int(df_all.sallregime[ip]),
                        #"erosionregime":int(df.erosionregime[ip])
                        })
                        )

        # Save xbeach geojson file for Sallenger regimes
        if features:
            feature_collection = FeatureCollection(features)
            output_path_regime = os.path.join(output_path, 'sallenger\\')
            fo.mkdir(output_path_regime)
            file_name = os.path.join(output_path_regime,
                                "sallenger.geojson.js")
            cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var regimes =")
    
        dct={}
        dct["name"]        = "sallenger"
        dct["long_name"]   = "Sallenger regimes XBeach"
        dct["description"] = "These are the Sallenger regimes"
        dct["format"]      = "geojson"
        dct["legend"] = make_legend(type = 'sallenger_regimes') 

        self.map_variables.append(dct)

        # now same for Erosion regimes
        features_ero = []    
        for ip in range(len(df_all)):
            lon, lat = transformer.transform(df_all.X[ip],df_all.Y[ip])
            point = Point((lon, lat))
                        
            features_ero.append(Feature(geometry=point,
            properties={"LocNr":int(ip),
                        "Lon":lon,
                        "Lat":lat,                                                
                        "regime":int(df_all.erosionregime[ip])}))

        # Save xbeach geojson file for erosion regimes
        if features_ero:
            feature_collection_ero = FeatureCollection(features_ero)
            output_path_regime = os.path.join(output_path, 'erosionregimes\\')
            fo.mkdir(output_path_regime)
            file_name = os.path.join(output_path_regime,
                                "erosionregimes.geojson.js")
            cht.misc.misc_tools.write_json_js(file_name, feature_collection_ero, "var regimes =")
    
        dct={}
        dct["name"]        = "erosion_regimes"
        dct["long_name"]   = "Erosion regimes XBeach"
        dct["description"] = "These are the Erosion regimes"
        dct["format"]      = "geojson"
        dct["legend"] = make_legend(type = 'erosion_regimes')
  
        self.map_variables.append(dct)


    def make_runup_map(self):        
        """Make runup markers and timeseries for webviewer.
        """   

        output_path = self.cycle_path

        # Extreme runup height

        for model in cosmos.scenario.model:
            if model.type == 'beware':
           
                try:
                    if os.path.exists(os.path.join(model.cycle_output_path,
                                            "beware_his.nc")) and not model.ensemble:

                        model.domain.read_data(os.path.join(model.cycle_output_path,
                                                            "beware_his.nc"))                
        
                        features = []
                        transformer = Transformer.from_crs(model.crs,
                                                        'WGS 84',
                                                        always_xy=True)
                        
                        for ip in range(len(model.domain.filename)):
                            x, y = transformer.transform(model.domain.xp[ip],
                                                        model.domain.yp[ip])
                            point = Point((x, y))
                            name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                        
                            id = np.argmax(model.domain.R2[ip,:])                                                                       
                            features.append(Feature(geometry=point,
                                                    properties={"model_name":model.name,
                                                                "LocNr":int(model.domain.filename[ip]),
                                                                "Lon":x,
                                                                "Lat":y,                                                
                                                                "Setup":round(model.domain.R2_setup[ip, id],2),
                                                                "Swash":round(model.domain.swash[ip, id],2),
                                                                "TWL":round(model.domain.R2[ip, id] + model.domain.WL[ip, id],2)}))
                                            
                        if features:
                            feature_collection = FeatureCollection(features)
                            output_path_runup =  os.path.join(output_path, 'extreme_runup_height\\')
                            fo.mkdir(output_path_runup)
                            file_name = os.path.join(output_path_runup,
                                                    "extreme_runup_height.geojson.js")
                            cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var runup =")
        
                        dct={}
                        dct["name"]        = "extreme_runup_height"
                        dct["long_name"]   = "Maximum Total Water Level (best track)"
                        dct["description"] = "These are the predicted total water levels"
                        dct["format"]      = "geojson"
                        dct["infographic"] = "twl"
        
                        dct["legend"] = make_legend(type = 'run_up')
   
        
                        self.map_variables.append(dct)
   
                    # Probabilistic runup

                    if os.path.exists(os.path.join(model.cycle_output_path,
                                                            "beware_his.nc")) and model.ensemble:
                        model.domain.read_data(os.path.join(model.cycle_output_path,
                                                            "beware_his.nc"), prcs= [5, 50, 95])                
        
                        features = []
                        transformer = Transformer.from_crs(model.crs,
                                                        'WGS 84',
                                                        always_xy=True)
                        
                        for ip in range(len(model.domain.filename)):
                            x, y = transformer.transform(model.domain.xp[ip],
                                                        model.domain.yp[ip])
                            point = Point((x, y))
                            name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                        
                            id = np.argmax(model.domain.R2[ip,:,0])                                                                       
                            features.append(Feature(geometry=point,
                                                    properties={"model_name":model.name,
                                                                "LocNr":int(model.domain.filename[ip]),
                                                                "Lon":x,
                                                                "Lat":y,                                                
                                                                "Setup":round(model.domain.R2_setup_prc["95"][ip, id],2),
                                                                "Swash":round(model.domain.swash[ip, id,0],2),
                                                                "TWL":round(model.domain.R2_prc["95"][ip, id]+model.domain.WL[ip, id,0],2)}))
                                                
                        if features:
                            feature_collection = FeatureCollection(features)
                            output_path_runup =  os.path.join(output_path, 'extreme_runup_height_prc95\\')
                            fo.mkdir(output_path_runup)
                            file_name = os.path.join(output_path_runup,
                                                    "extreme_runup_height_prc95.geojson.js")
                            cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var runup_prc95 =")
        
                        dct={}
                        dct["name"]        = "extreme_runup_height_prc95"
                        dct["long_name"]   = "Maximum Total Water Level (95 % of ensemble)"
                        dct["description"] = "These are the predicted extreme run-up heights"
                        dct["format"]      = "geojson"
                        dct["infographic"]   = "twl"
        
                        dct["legend"] = make_legend(type = 'run_up')        
            
                        self.map_variables.append(dct)

                    # Offshore water level and wave height
                    if not model.ensemble:
                        features = []
                            
                        for ip in range(len(model.domain.filename)):
                            x, y = transformer.transform(model.domain.xo[ip],
                                                        model.domain.yo[ip])
                            point = Point((x, y))
                            name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                        
                            id = np.argmax(model.domain.R2[ip,:])                                                               
                            features.append(Feature(geometry=point,
                                                    properties={"model_name":model.name,
                                                                "LocNr":int(model.domain.filename[ip]),
                                                                "Lon": round(x,3),
                                                                "Lat": round(y,3),
                                                                "Hs":round(model.domain.Hs[ip, id],2),
                                                                "Tp":round(model.domain.Tp[ip, id],1),
                                                                "WL":round(model.domain.WL[ip, id],2)}))
                            
                        if features:
                            feature_collection = FeatureCollection(features)
                            output_path_waves =  os.path.join(output_path, 'extreme_sea_level_and_wave_height\\')
                            fo.mkdir(output_path_waves)
                            file_name = os.path.join(output_path_waves,     
                                                    "extreme_sea_level_and_wave_height.geojson.js")
                            cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var swl =")


                        dct={}
                        dct["name"]        = "extreme_sea_level_and_wave_height"
                        dct["long_name"]   = "Offshore WL and Hs"
                        dct["description"] = "This is the total offshore water level (tide + surge) and wave conditions."
                        dct["format"]      = "geojson"
                        dct["legend"]      = {"text": "Offshore Hs", "contours": [{"text": " 0.0&nbsp-&nbsp;1.0&#8201;m", "color": "#CCFFFF"}, {"text": " 1.0&nbsp;-&nbsp;3.0&#8201;m", "color": "#40E0D0"}, {"text": " 3.0&nbsp-&nbsp;5.0&#8201;m", "color": "#00BFFF"}, {"text": "&gt; 5.0&#8201;m", "color": "#0909FF"}]}
                        dct["infographic"]   = "offshore"

                        self.map_variables.append(dct)


                        # Horizontal runup

                        features = []
                        
                        dfx = pd.read_csv(os.path.join(model.path, 'input', 'runup.x'), index_col=0,
                            delim_whitespace=True)
                        dfy = pd.read_csv(os.path.join(model.path, 'input', 'runup.y'), index_col=0,
                            delim_whitespace=True)                    
                        r2max= dfx.columns.values

                        for ip in range(len(model.domain.filename)):
                        
                            name = 'Loc nr: ' +  str(model.domain.filename[ip])
                                        
                            id = np.argmax(model.domain.R2[ip,:])   

                            id2= np.argwhere(r2max.astype(float)>=model.domain.R2[ip,id])[0]
                            
                            x, y = transformer.transform(dfx[r2max[id2]].values[ip][0],
                                                        dfy[r2max[id2]].values[ip][0])
                            point = Point((x, y))

                            features.append(Feature(geometry=point,
                                                    properties={"model_name":model.name,
                                                                "LocNr":int(model.domain.filename[ip]),
                                                                "Lon":x,
                                                                "Lat":y,                                                
                                                                "Setup":round(model.domain.R2_setup[ip, id],2),
                                                                "Swash":round(model.domain.swash[ip, id],2),
                                                                "TWL":round(model.domain.R2[ip, id] + model.domain.WL[ip, id],2)}))

                        if features:
                            feature_collection = FeatureCollection(features)
                            output_path_runup =  os.path.join(output_path, 'extreme_horizontal_runup_height\\')
                            fo.mkdir(output_path_runup)
                            file_name = os.path.join(output_path_runup,     
                                                    "extreme_horizontal_runup_height.geojson.js")
                            cht.misc.misc_tools.write_json_js(file_name, feature_collection, "var runup_vert =")


                        dct={}
                        dct["name"]        = "extreme_horizontal_runup_height"
                        dct["long_name"]   = "Horizontal extent of Total Water Level"
                        dct["description"] = "This is the extreme horizontal runup."
                        dct["format"]      = "geojson"
                        dct["infographic"]   = "twl_hor"
                        # dct["legend"]      = {"text": "Offshore WL", "contours": [{"text": " 0.0&nbsp-&nbsp;0.33&#8201;m", "color": "#CCFFFF"}, {"text": " 0.33&nbsp;-&nbsp;1.0&#8201;m", "color": "#40E0D0"}, {"text": " 1.0&nbsp-&nbsp;2.0&#8201;m", "color": "#00BFFF"}, {"text": "&gt; 2.0&#8201;m", "color": "#0909FF"}]}
                        
                        dct["legend"] = make_legend(type = 'run_up')


                        self.map_variables.append(dct)                
                

                    # Time series 
                        
                    # for ip in range(len(model.domain.filename)):
                        
                    #     if os.path.exists(os.path.join(model.cycle_output_path,
                    #                                         "beware_his_ensemble.nc")):  
                    #         d= {'WL': model.domain.WL[ip,:],'Setup': model.domain.setup[ip,:], 'Swash': model.domain.swash[ip,:], 'Runup': model.domain.R2p[ip,:],
                    #             'Setup_5': model.domain.setup_prc["5"][ip,:],'Setup_50': model.domain.setup_prc["50"][ip,:],'Setup_95': model.domain.setup_prc["95"][ip,:],
                    #             'Runup_5': model.domain.R2p_prc["5"][ip,:],'Runup_50': model.domain.R2p_prc["50"][ip,:],'Runup_95': model.domain.R2p_prc["95"][ip,:],}       
                    #     else:
                    #         d= {'WL': model.domain.WL[ip,:],'Setup': model.domain.setup[ip,:], 'Swash': model.domain.swash[ip,:], 'Runup': model.domain.R2p[ip,:]}       
            
                    #     v= pd.DataFrame(data=d, index =  pd.date_range(model.domain.input.tstart, periods=len(model.domain.swash[ip,:]), freq= '0.5H'))
                    #     obs_file = "extreme_runup_height." + model.domain.runid + "." +str(model.domain.filename[ip]) + ".csv.js"
            
                    #     local_file_path = os.path.join(output_path,  "timeseries",
                    #                                        obs_file)
                    #     s= v.to_csv(path_or_buf=None,
                    #                  date_format='%Y-%m-%dT%H:%M:%S',
                    #                  float_format='%.3f',
                    #                  header= False, index_label= 'datetime') 
                               
                    #     if os.path.exists(os.path.join(model.cycle_output_path, "beware_his_ensemble.nc")):
                    #         cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup, setup_5, setup_50, setup_95, runup_5, runup_50, runup_95")
                    #     else:
                    #         cht.misc.misc_tools.write_csv_js(local_file_path, s, "var csv = `date_time,wl,setup,swash,runup")

                except:
                    cosmos.log("An error occurred when making BEWARE webviewer !")

    def make_timeseries(self, ts_type):
        """Generic function to make time series for the webviewer."""        
        if ts_type == "waves":
            station_type = "wave_buoy"
            var_string = "hm0,tp"
            station_file = "wavebuoys.geojson.js"
            station_var = "buoys"
        elif ts_type == "wl":    
            station_type = "tide_gauge"
            var_string = "wl"
            station_file = "stations.geojson.js"
            station_var = "stations"
        features = []    
        for model in cosmos.scenario.model:
            if model.station:
                for station in model.station:
                    if station.type == station_type and station.upload:                
                        point = Point((station.longitude, station.latitude))
                        if station.id:
                            name = station.long_name + " (" + station.id + ")"
                        else:
                            name = station.long_name
    
                        path = cosmos.scenario.path
                        t0 = cosmos.cycle - datetime.timedelta(hours=48)
                        t1 = cosmos.cycle
                        t0_obs = t0
                        t1_obs = cosmos.stop_time
                        cmp_file = None
                        obs_file = None
                        
                        # Merge time series from previous cycles
                        v  = merge_timeseries(path, model.name, station.name, ts_type,
                                                   t0=t0.replace(tzinfo=None),
                                                   t1=t1.replace(tzinfo=None))
                        
                        # Check if merge returned values
                        if v is not None:                            
                            # Correct to MSL if necessary
                            if ts_type == "wl":
                                v += model.vertical_reference_level_difference_with_msl
                            # Write csv js file
                            cmp_file = ts_type + "." + station.name + "." + model.name + ".csv.js"
                            csv_file = os.path.join(self.cycle_path,
                                                    "timeseries",
                                                    cmp_file)
                            s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                         float_format='%.3f',
                                         header=False) 
                            
                            if model.ensemble:
                                if ts_type == "waves":
                                    var_string2 =  "hm0_5,tp_5,hm0_50,tp_50,hm0_95,tp_95"
                                elif ts_type == "wl":
                                    var_string2 = "wl_5,wl_50,wl_95"
                            else:
                                var_string2=var_string
                            cht.misc.misc_tools.write_csv_js(csv_file, s, "var csv = `date_time," + var_string2)

                        # Check if there are observations
                        if cosmos.scenario.observations_path and station.id:
                            obs_pth = os.path.join(cosmos.config.path.main,
                                               "observations",
                                               cosmos.scenario.observations_path,
                                               ts_type)                        
                            csv_file = ts_type + "." + station.id + ".observed.csv.js"
                            if os.path.exists(os.path.join(obs_pth, csv_file)):

                                # Read in csv file to a dataframe
                                df = pd.read_csv(os.path.join(obs_pth, csv_file),
                                                index_col=0,
                                                parse_dates=True,
                                                skipfooter=1)
                                # Cut off time series to same time as model
                                mask = (df.index >= t0_obs.replace(tzinfo=None) - datetime.timedelta(hours=1)) & (df.index <= t1_obs.replace(tzinfo=None) + datetime.timedelta(hours=1))
                                df = df.loc[mask]
                                # Check if df is not empty
                                if not df.empty:                         
                                    # Convert to csv
                                    s = df.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                                float_format='%.3f',
                                                header=False) 
                                    # Write csv js file
                                    obs_file = csv_file
                                    cht.misc.misc_tools.write_csv_js(os.path.join(self.cycle_path, "timeseries", obs_file),
                                                                    s,
                                                                    "var csv = `date_time," + var_string)
                                
                                
                        if cmp_file or obs_file:
                            features.append(Feature(geometry=point,
                                                    properties={"name":station.name,
                                                                "long_name":name,
                                                                "id":station.id,
                                                                "model_name":model.name,
                                                                "model_type":model.type,
                                                                "model_ensemble": model.ensemble,
                                                                "mllw":station.mllw,
                                                                "cycle": cosmos.cycle_string,
                                                                "cmp_file":cmp_file,
                                                                "obs_file":obs_file}))
        if features:
            feature_collection = FeatureCollection(features)
            buoys_file = os.path.join(self.cycle_path, station_file)
            cht.misc.misc_tools.write_json_js(buoys_file, feature_collection, "var " + station_var + " =")

    def update_scenarios_js(self, other_js_source = None):
        # Check if there is a scenarios.js file
        # If so, append it with the current scenario

        if other_js_source:
            sc_file = os.path.join(other_js_source)
        else:
            sc_file = os.path.join(self.path, "data", "scenarios.js")
            
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
        newsc["cycle"]       = cosmos.cycle.strftime('%Y-%m-%dT%H:%M:%S')
        newsc["cycle_string"] = cosmos.cycle_string
        newsc["cycle_mode"]  = cosmos.config.cycle.mode
        newsc["duration"]    = str(cosmos.scenario.runtime)
        now = datetime.datetime.utcnow()
        newsc["last_update"] = now.strftime("%Y/%m/%d %H:%M:%S" + " (UTC)")
        if isame>-1:
            # Scenario already existed in web viewer
            scs[isame] = newsc
        else:
            # New scenario in web viewer    
            scs.append(newsc)        

        cht.misc.misc_tools.write_json_js(sc_file, scs, "var scenario =")

    def upload(self):
        if cosmos.config.cycle.run_mode == "cloud":
            # Upload to S3
            self.upload_to_s3()

        elif cosmos.config.cycle.run_mode == "parallel":
            self.copy_to_opendap()

        elif cosmos.config.cycle.run_mode == "serial": # Test
            self.copy_to_opendap()

        else:
            self.upload_to_opendap()
            
    def upload_to_opendap(self):    
        """Upload web viewer to web server."""
        from cht.misc.sftp import SSHSession        
        cosmos.log("Uploading web viewer to OpenDap ...")        
        # Upload entire copy of local web viewer to web server        
        try:
            f = SSHSession(cosmos.config.webserver.hostname,
                           username=cosmos.config.webserver.username,
                           password=cosmos.config.webserver.password)
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
                if not self.name in f.sftp.listdir(cosmos.config.webserver.path):
                    make_wv_on_ftp = True
                    
            if make_wv_on_ftp:
                # Copy entire webviewer
                f.put_all(self.path, cosmos.config.webserver.path)
    
            else:
                # Webviewer already on ftp server
                
                remote_path = cosmos.config.webserver.path + "/" + self.name + "/data" 
                # Check if scenario is already on ftp server
                cosmos.log("Removing existing data on web server ...")
                if cosmos.scenario.name in f.sftp.listdir(remote_path):
                    f.rmtree(remote_path + "/" + cosmos.scenario.name)
                    
                # Copy scenarios.js    
                remote_file = remote_path + "/scenarios.js"
                local_file  = os.path.join(".", "scenarios.js")
                f.get(remote_file, local_file)
                self.update_scenarios_js(local_file)                
                # Copy new scenarios.js to server
                f.put(local_file, remote_path + "/scenarios.js")
                # Delete local scenarios.js
                fo.rm(local_file)

                # Copy scenario data to server
                cosmos.log("Uploading all data to web server ...")
                f.put_all(self.cycle_path, remote_path)
            
            f.sftp.close()    
    
            cosmos.log("Done uploading.")
            
        except BaseException as e:
            cosmos.log("An error occurred while uploading !")
            cosmos.log(str(e))
            
            try:
                f.sftp.close()    
            except:
                pass

    def copy_to_opendap(self):
        cosmos.log("Copying webviewer to OpenDap ...")

        # Upload entire copy of local web viewer to web server

        try:
            # Check if web viewer already exist
            make_wv_on_ftp = False
            if not self.exists:
                # Web viewer does not even exist locally
                make_wv_on_ftp = True
            else:
                # Check if web viewer exists on FTP
                if not self.name in os.listdir(cosmos.config.webserver.path):
                    make_wv_on_ftp = True
                
            if make_wv_on_ftp:
                # Copy entire webviewer
                shutil.copytree(self.path, cosmos.config.webserver.path)    
            else:
                # Webviewer already on ftp server
    
                # Only copy scenario output
                remote_path = os.path.join(cosmos.config.webserver.path, self.name, "data")

                # Check if scenario is already on ftp-server

                if os.path.exists(os.path.join(remote_path, cosmos.scenario.name)):

                    # Check if scenario-cycle is already on ftp server
                    if cosmos.cycle_string in os.listdir(os.path.join(remote_path, cosmos.scenario.name)):
                        cosmos.log("Removing cycle {} from web server ...".format(cosmos.cycle_string))
                        shutil.rmtree(os.path.join(remote_path, cosmos.scenario.name, cosmos.cycle_string))
                    
                # Copy scenarios.js    
                remote_file = os.path.join(remote_path, "scenarios.js")
                local_file  = os.path.join(".", "scenarios.js")

                shutil.copyfile(remote_file, local_file)
                self.update_scenarios_js(local_file)  # Why do we need to update local scenario.js file? The scneario should be already in there.
                # Copy new scenarios.js to server
                shutil.copyfile(local_file, remote_file)
                # Delete local scenarios.js
                fo.rm(local_file) # Why delete local file?

                # Copy scenario data to server
                cosmos.log("Uploading all data to web server ...")
                shutil.copytree(self.cycle_path, os.path.join(remote_path, cosmos.scenario.name, cosmos.cycle_string))
                
            cosmos.log("Done copying.")

            #TODO add deletion of older cycles?
            
        except BaseException as e:
            cosmos.log("An error occurred while copying !")
            cosmos.log(str(e))

    def upload_to_s3(self):    
        """Upload web viewer to S3"""
        cosmos.log("Uploading web viewer to S3 ...")        
        try:
            # Upload entire copy of local web viewer to web server
            bucket_name = "scenario-webviewer"
#            bucket_name = "cosmos.deltares.nl"
            local_folder = self.cycle_path
            s3_folder = self.name + "/" + "data" + "/" + cosmos.scenario.name + "/" + cosmos.cycle_string
            cosmos.cloud.upload_folder(bucket_name, local_folder, s3_folder)
            # Upload scenarios.js
            local_file = os.path.join(self.path, "data", "scenarios.js")
            s3_folder  = self.name + "/" + "data"
            cosmos.cloud.upload_file(bucket_name, local_file, s3_folder)
        except BaseException as e:
            cosmos.log("An error occurred while uploading !")
            cosmos.log(str(e))

def merge_timeseries(path, model_name, station, prefix,
                        t0=None,
                        t1=None,
                        resample=None):
    
    name_str = prefix
    available_times = []    
    cycle_list = fo.list_folders(os.path.join(path,'*z'))
    for it, cycle_string in enumerate(cycle_list):
        available_times.append(datetime.datetime.strptime(cycle_list[it][-12:],"%Y%m%d_%Hz"))
    if t0==None or t1==None:
        t0 = available_times[0]
        t1 = available_times[-1]
            
    # New pandas series
    wl=[]
    idx=[]
    wl.append(0.0)
    idx.append(pd.Timestamp("2100-01-01"))
    vv = pd.Series(wl, index=idx)
    vv.index.name = "date_time"
    vv.name       = name_str
    okay = False
    for it, t in enumerate(available_times):        
        if t>=t0 and t<=t1:                       
            csv_file = os.path.join(path,
                                    cycle_list[it][-12:],
                                    "models",
                                    model_name,
                                    "timeseries",
                                    prefix + "." + station + ".csv")
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, header=0,
                                index_col=0,
                                parse_dates=True).squeeze()
                df.index.name = "date_time"
                df.name       = name_str                    
                okay = True
                # Find last time in merged time series that is smaller than first time in new timeseries
                ilast = np.where(vv.index<df.index[0])[-1]
                if ilast.any():
                    ilast = ilast[-1]
                    vv = vv[0:ilast]
                    vv = vv.append(df)
                else:
                    vv = df
                    
    if okay:                                                
        if resample:                        
            t0 = (vv.index - vv.index[0]).total_seconds()
            t1 = np.arange(0.0,t0[-1], resample)
            f  = interpolate.interp1d(t0, vv)
            v1 = f(t1)
            t1 = vv.index[0] + t1*datetime.timedelta(seconds=1)                
            vv = pd.Series(v1, index=t1)
            vv.index.name = "date_time"
            vv.name       = name_str                            
    if okay:                                    
        return vv                
    else:
        return None

def make_legend(type:str = None, mp=None):
    if type:    
        mp = next((cosmos.config.map_contours[x] for x in cosmos.config.map_contours if x == type), None)    

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

    return lgn
# -*- coding: utf-8 -*-
"""
Created on Sat May 29 10:28:52 2021

@author: ormondt
"""

import os
import numpy as np
import pandas as pd
import datetime

from .cosmos_main import cosmos
from .cosmos_webviewer import WebViewer
from .cosmos_tiling import make_wave_map_tiles

def post_process():

    # if cosmos.config.make_figures:
    #     make_waterlevel_figure()

    
    # Make wave map tiles
    if cosmos.config.make_wave_maps and not cosmos.config.webviewer:
        # First determine max wave height for all simulations 
        hm0mx = 0.0
        for model in cosmos.scenario.model:
            index_path = os.path.join(model.path, "tiling", "indices")
            if model.make_wave_map and os.path.exists(index_path):
                if "sfincs" in model.name.lower():
                    continue
                file_name = os.path.join(model.cycle_output_path, "hurrywave_map.nc")
                hm0max = model.domain.read_hm0max(hm0max_file=file_name)
                hm0mx = max(hm0mx, np.max(hm0max))
                                
        # Set color scale        
        if hm0mx<=2.0:
            contour_set = "Hm0_2m"
        elif hm0mx<=5.0:   
            contour_set = "Hm0_5m"
        elif hm0mx<=10.0:   
            contour_set = "Hm0_10m"
        elif hm0mx<=20.0:   
            contour_set = "Hm0_10m"
            
        for model in cosmos.scenario.model:
            index_path = os.path.join(model.path, "tiling", "indices")            
            if model.make_wave_map and os.path.exists(index_path):
                if "sfincs" in model.name.lower():
                    continue                            
                file_name = os.path.join(model.cycle_output_path, "hurrywave_map.nc")

                # Wave map for the entire simulation
                dt1 = datetime.timedelta(hours=1)
                dt6 = datetime.timedelta(hours=6)
                dt7 = datetime.timedelta(hours=7)
                t0 = cosmos.cycle_time.replace(tzinfo=None)    
                t1 = cosmos.stop_time
                tr = [t0 + dt7, t1 + dt1]
                tstr = "combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ")
                ttlstr = "Combined 48-hour forecast"

                hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                            "hm0",
                                            tstr)

                hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                                                 time_range=tr)
    
                make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)

                # Wave map over 6-hour increments
                
                # Loop through time
                t0 = cosmos.cycle_time.replace(tzinfo=None)    
                requested_times = pd.date_range(start=t0 + dt6,
                                                end=t1,
                                                freq='6H').to_pydatetime().tolist()
                
                cosmos.log("Making wave map tiles ...")    
                for it, t in enumerate(requested_times):
                    tr = [t - dt1, t + dt1]
                    hm0max = model.domain.read_hm0max(hm0max_file=file_name,
                                                      time_range=tr)
                    
                    tstr = (t - dt6).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ")
                    ttlstr = (t - dt6).strftime("%Y-%m-%d %H:%M") + " - " + (t).strftime("%Y-%m-%d %H:%M") + " UTC"
                    hm0_map_path = os.path.join(cosmos.scenario.cycle_tiles_path,
                                                "hm0",
                                                tstr)
                    
                    make_wave_map_tiles(hm0max, index_path, hm0_map_path, contour_set)

                cosmos.log("Wave map tiles done.")    


    
    if cosmos.config.webviewer:
        # Build new web viewer, or copy scenario data to existing viewer
        
        wv = WebViewer(cosmos.config.webviewer)
        wv.make()
        
        if cosmos.config.upload:
            current_path = os.getcwd()
            try:
                wv.upload()
            except:
                print("An error occurred when uploading web viewer to server !!!")
            os.chdir(current_path)

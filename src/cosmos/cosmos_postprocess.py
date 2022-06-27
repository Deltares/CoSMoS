# -*- coding: utf-8 -*-
"""
Created on Sat May 29 10:28:52 2021

@author: ormondt
"""

import os

from .cosmos_main import cosmos
from .cosmos_webviewer import WebViewer

def post_process():

    # if cosmos.config.make_figures:
    #     make_waterlevel_figure()
    
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

# def make_waterlevel_figure():

#     model_name = "sfincs_charleston"
    
#     for model in cosmos.scenario.model:

#         if model.name == model_name:
            
#             figure_path = os.path.join(model.cycle_path,
#                                        "figures")
#             output_path = os.path.join(model.cycle_path,
#                                        "output")
#             floodmap_path = os.path.join(model.cycle_path,
#                                        "floodmap")
            
#             zstfile = os.path.join(output_path, "zst.txt")
#             if not model.domain.input.tref:
#                 model.domain.input.tref = cosmos.scenario.ref_date

#             v = model.domain.read_timeseries_output(file_name=zstfile)
            
#             # Get observations
#             t0 = cosmos.cycle_time - datetime.timedelta(days=3)
#             t0 = t0.replace(hour=0)
#             t1 = model.flow_stop_time.replace(hour=0)
#             t1 = t1 + datetime.timedelta(days=1)
#             t0_string = t0.strftime("%Y%m%d")                
#             t1_string = t1.strftime("%Y%m%d")                
            
#             try:
#                 import noaa_coops as nc
            
#                 charleston = nc.Station(8665530)
#                 obs = charleston.get_data(begin_date=t0_string,
#                                                       end_date=t1_string,
#                                                       product="water_level",
#                                                       datum="MSL",
#                                                       units="metric",
#                                                       time_zone="gmt")
                
#                 prd = charleston.get_data(begin_date=t0_string,
#                                                       end_date=t1_string,
#                                                       product="predictions",
#                                                       datum="MSL",
#                                                       units="metric",
#                                                       time_zone="gmt")
                    
#                 v   = (  v + 0.89)/0.3048 
#                 prd.predicted_wl = (prd.predicted_wl + 0.89)/0.3048 
#                 obs.water_level = (obs.water_level + 0.89)/0.3048 
    
#                 fig, ax = plt.subplots()
    
#                 prd.predicted_wl.plot(ax=ax, label='predicted')
#                 obs.water_level.plot(ax=ax, label='observed')
#                 v.plot(ax=ax, label='computed')
    
#                 ax.legend()
#                 ax.set_title("Water level Charleston (forecast cycle: " + cosmos.cycle_string + ")")
                
#                 t0 = cosmos.cycle_time - datetime.timedelta(days=1)
#                 t1 = model.flow_stop_time
                
#                 ax.set_xlim([t0, t1])
#                 ax.yaxis.set_major_locator(MultipleLocator(0.5))
#     #            ax.set_xlim([-2.0, 10.0])
                
#                 plt.grid(True)
#                 plt.ylabel("Height in feet (MLLW)")
    
#                 plt.show()
                
#                 png_file = os.path.join(figure_path, "charleston_forecast.png")
#                 plt.savefig(png_file, dpi=100)
                
#                 plt.close()
     
#             except:
#                 pass
            
#             # if cosmos.config.make_floodmaps:

#             #     # Floodmap            
#             #     from tiling import make_png_tiles
#             #     from pyproj import CRS
    
#             #     # Compute lon/lat range
#             #     model.crs = CRS("WGS 84 / UTM zone 18N")
#             #     # Read zs max
#             #     t0 = cosmos.cycle_time + datetime.timedelta(hours=1)
#             #     t1 = model.flow_stop_time
                
#             #     zsmax=model.domain.read_zsmax(zsmax_file = os.path.join(output_path, "zsmax.dat"),
#             #                                   time_range=[t0.replace(tzinfo=None),
#             #                                               t1.replace(tzinfo=None)])
    
#             #     # Difference between MSL and NAVD88 (used in topo data)
#             #     zsmax -= 0.067 
                 
#             #     zoom_range = [0, 14]
#             #     index_path = os.path.join(model.path, "tiling", "indices")
#             #     topo_path = os.path.join(model.path, "tiling", "topobathy")
                
#             #     color_values=[]
                
#             #     color_value = {}
#             #     color_value["lower_value"] = 0.05
#             #     color_value["upper_value"] = 0.30
#             #     #color_value["rgb"] = [51, 204, 255]
#             #     color_value["rgb"] = [ 0, 255,   0]
#             #     color_values.append(color_value)
                
#             #     color_value = {}
#             #     color_value["lower_value"] = 0.30
#             #     color_value["upper_value"] = 1.00
#             #     #color_value["rgb"] = [51, 102, 255]
#             #     color_value["rgb"] = [255, 255, 0]
#             #     color_values.append(color_value)
                
#             #     color_value = {}
#             #     color_value["lower_value"] = 1.00
#             #     color_value["upper_value"] = 1000.0
#             #     color_value["rgb"] = [255, 0, 0]
#             #     color_values.append(color_value)
                
#             #     make_tiles(zsmax, index_path, floodmap_path,
#             #                 topo_path=topo_path,
#             #                 zoom_range=zoom_range,
#             #                 option="floodmap",
#             #                 color_values=color_values,
#             #                 zbmax=1.0)




# def upload_latest_json(f):
    
#     # Cycle information in latest.json    
#     cosmos.log("Uploading latest.json ...")
#     tstr = cosmos.cycle_time.strftime('%Y-%m-%dT%H:%M:%S')
#     x = {
#       "cycle": tstr,
#       "duration": str(cosmos.scenario.run_duration),
#       "type": "forecast"
#     }       
#     y = json.dumps(x)       
#     fid = open("latest.json", "w")
#     fid.write(y)
#     fid.close()
#     source_path = "latest.json"
#     target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/latest.json"
#     f.put(source_path, target_path)

# def upload_tide_gauges(f):

#     target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/timeseries"
#     try:
#         f.sftp.mkdir(target_path)
#     except:
#         pass    
    
#     features = []

#     # Tide stations
#     for model in cosmos.scenario.model:
#         if model.station and model.flow:
#             for station in model.station:                
#                 if station.type == "tide_gauge" and station.upload:
                
#                     point = Point((station.longitude, station.latitude))
#                     name = station.long_name + " (" + station.id + ")"
                    
#                     # Check if there is a file in the observations that matches this station
#                     obs_file = None
#                     if cosmos.scenario.observations_path and station.id:
#                         obs_pth = os.path.join(cosmos.config.main_path,
#                                            "observations",
#                                            cosmos.scenario.observations_path,
#                                            "water_levels")                        
#                         fname = "waterlevel." + station.id + ".observed.csv"
#                         if os.path.exists(os.path.join(obs_pth, fname)):
#                             obs_file = fname
                                                                    
#                     features.append(Feature(geometry=point,
#                                             properties={"name":station.name,
#                                                         "long_name":name,
#                                                         "id": station.id,
#                                                         "mllw":station.mllw,
#                                                         "model_name":model.name,
#                                                         "model_type":model.type,
#                                                         "obs_file":obs_file}))
                    
#                     # Merge time series from previous cycles
#                     # Go two days back
#                     path = model.archive_path
#                     t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
#                     t1 = cosmos.cycle_time
#                     v  = merge(path,
#                                station.name,
#                                t0=t0.replace(tzinfo=None),
#                                t1=t1.replace(tzinfo=None),
#                                prefix='waterlevel')
                    
#                     v += model.vertical_reference_level_difference_with_msl
                    
#                     csv_file = "waterlevel." + model.name + "." + station.name + ".csv"
#                     local_file_path = os.path.join(cosmos.temp_path,
#                                                    csv_file)
#                     v.to_csv(local_file_path,
#                              date_format='%Y-%m-%dT%H:%M:%S',
#                              float_format='%.3f')        
    
#                     cosmos.log("Uploading water levels in " + csv_file + " ...")
#                     remote_file_path = cosmos.config.ftp_path + "/"  + cosmos.scenario.name + "/timeseries/" + csv_file

#                     f.put(local_file_path, remote_file_path)
#                     if obs_file:
#                         remote_file_path = cosmos.config.ftp_path + "/"  + cosmos.scenario.name + "/timeseries/" + obs_file
#                         f.put(os.path.join(obs_pth, obs_file), remote_file_path)

#     cosmos.log("Uploading stations.geojson ...")
#     feature_collection = FeatureCollection(features)
#     with open('stations.geojson', 'w') as fl:
#         dump(feature_collection, fl)
#     local_file_path = "stations.geojson"
#     remote_file_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/stations.geojson"
#     f.put(local_file_path, remote_file_path)

# def upload_wave_buoys(f):
    
#     target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/timeseries"
#     try:
#         f.sftp.mkdir(target_path)
#     except:
#         pass    

#     features = []

#     # Wave buoys
#     for model in cosmos.scenario.model:
#         if model.station and model.wave:
#             for station in model.station:
#                 if station.type == "wave_buoy" and station.upload:                
#                     point = Point((station.longitude, station.latitude))
#                     if station.ndbc_id:
#                         name = station.long_name + " (" + station.ndbc_id + ")"
#                     else:
#                         name = station.long_name
#                     features.append(Feature(geometry=point,
#                                             properties={"name":station.name,
#                                                         "long_name":name,
#                                                         "id": station.ndbc_id,
#                                                         "model_name":model.name,
#                                                         "model_type":model.type}))

#                     path = model.archive_path
#                     t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
#                     t1 = cosmos.cycle_time
                    
#                     # Hm0
#                     v  = merge(path,
#                                station.name,
#                                t0=t0.replace(tzinfo=None),
#                                t1=t1.replace(tzinfo=None),
#                                prefix='hm0')
                    
#                     csv_file = "hm0." + station.name + ".csv"
#                     local_file_path = os.path.join(cosmos.temp_path,
#                                                    csv_file)
#                     v.to_csv(local_file_path,
#                              date_format='%Y-%m-%dT%H:%M:%S',
#                              float_format='%.3f')        
    
#                     cosmos.log("Uploading wave heights in " + csv_file + " ...")
#                     remote_file_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/timeseries/" + csv_file
#                     f.put(local_file_path, remote_file_path)

#                     # Tp
#                     v  = merge(path,
#                                station.name,
#                                t0=t0.replace(tzinfo=None),
#                                t1=t1.replace(tzinfo=None),
#                                prefix='tp')
                    
#                     csv_file = "tp." + station.name + ".csv"
#                     local_file_path = os.path.join(cosmos.temp_path,
#                                                    csv_file)
#                     v.to_csv(local_file_path,
#                              date_format='%Y-%m-%dT%H:%M:%S',
#                              float_format='%.3f')        
    
#                     cosmos.log("Uploading wave periods in " + csv_file + " ...")
#                     remote_file_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/timeseries/" + csv_file
#                     f.put(local_file_path, remote_file_path)

#     cosmos.log("Uploading wavebuoys.geojson ...")
#     feature_collection = FeatureCollection(features)
#     with open('wavebuoys.geojson', 'w') as fl:
#         dump(feature_collection, fl)
#     local_file_path = "wavebuoys.geojson"
#     remote_file_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/wavebuoys.geojson"
#     f.put(local_file_path, remote_file_path)

# def upload_wind_fields(f):

#     # Winds in JSON wind file
#     subset = cosmos.scenario.model[0].meteo_subset
#     dx = subset.x[1] - subset.x[0]
#     stride = int(0.5/dx)
#     time_range = [cosmos.cycle_time.replace(tzinfo=None),                          
#                   cosmos.cycle_time.replace(tzinfo=None) + datetime.timedelta(hours=cosmos.scenario.run_duration)]
#     json_set = subset.subset(time_range=time_range,
#                                        stride=stride)
#     cosmos.log("Uploading winds in gfs_conus.json ...")
#     json_set.write_wind_to_json("gfs_conus.json",
#                                 time_range=time_range)
#     source_path = "gfs_conus.json"
#     target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/gfs_conus.json"
#     f.put(source_path, target_path)

# def upload_png_tiles(f):

#     source_path = os.path.join(cosmos.scenario.path, "tiles", "floodmap")
#     if cosmos.config.make_flood_maps and os.path.exists(source_path):
#         cosmos.log("Uploading floodmap tiles ...")
#         target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/tiles"
#         # First delete existing folder
#         try:
#             print("Trying to delete existing tiles ...")
#             f.rmtree(target_path + "/floodmap")
#         except:
#             print("Well, that didn't work ...")
#             pass
#         try:
#             f.sftp.mkdir(target_path)
#         except:
#             print("Could not make folder " + target_path)
#             pass
#         try:             
#             f.put_all(source_path, target_path)
#         except:
#             print("Error uploading tiles ...")
#             pass

#     source_path = os.path.join(cosmos.scenario.path, "tiles", "hm0")
#     if cosmos.config.make_wave_maps and os.path.exists(source_path):
#         cosmos.log("Uploading Hm0 tiles ...")
#         target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/tiles"
#         try:
#             f.sftp.mkdir(target_path)
#         except:
#             pass
#         f.put_all(source_path, target_path)

#     source_path = os.path.join(cosmos.scenario.path, "tiles", "tp0")
#     if cosmos.config.make_wave_maps and os.path.exists(source_path):
#         cosmos.log("Uploading Tp tiles ...")
#         target_path = cosmos.config.ftp_path + "/" + cosmos.scenario.name + "/tiles"
#         try:
#             f.sftp.mkdir(target_path)
#         except:
#             pass
#         f.put_all(source_path, target_path)

# def rmtree(sftp, remotepath, level=0):
#     for f in sftp.listdir_attr(remotepath):
#         rpath = posixpath.join(remotepath, f.filename)
#         if stat.S_ISDIR(f.st_mode):
#             rmtree(sftp, rpath, level=(level + 1))
#         else:
#             rpath = posixpath.join(remotepath, f.filename)
#             print('removing %s%s' % ('    ' * level, rpath))
#             sftp.remove(rpath)
#     print('removing %s%s' % ('    ' * level, remotepath))
#     sftp.rmdir(remotepath)

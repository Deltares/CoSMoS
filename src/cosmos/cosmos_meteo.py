# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:28:58 2021

@author: ormondt
"""
import os
import glob
from pyproj import CRS
import numpy as np
import datetime

from .cosmos_main import cosmos
from cht_meteo.cht.meteo.meteo import MeteoSource
from cht_meteo.cht.meteo.meteo import MeteoGrid
import toml
import cht_utils.fileops as fo
from cht_cyclones.tropical_cyclone import TropicalCyclone

def read_meteo_sources():
    """Read meteo sources from ../meteo/meteo_subsets.toml.
    """    
    
    # Read meteo sources
    cosmos.meteo_source = []
    cosmos.meteo_subset = []

    # These are hard-coded for now !
    src = MeteoSource("gfs_forecast_0p25",
                      "gfs_forecast_0p25",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6)
    cosmos.meteo_source.append(src)

    src = MeteoSource("gfs_anl_0p50",
                      "gfs_anl_0p50_04",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_analysis",
                      "coamps_analysis",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_ufl_d01",
                      "coamps_tc_ufl_d01",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6,
                      cycle_interval=12,
                      time_interval=1)
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_hindcast",
                      "coamps_tc_hindcast",
                      "analysis",
                      crs=CRS.from_epsg(4326))
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_forecast",
                      "coamps_tc_forecast",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6,
                      config_path=cosmos.config.metget_config_path)
    cosmos.meteo_source.append(src)

    src = MeteoSource("coamps_tc_retro_forecast",
                      "coamps_tc_retro_forecast",
                      "forecast",
                      crs=CRS.from_epsg(4326),
                      delay=6)
    cosmos.meteo_source.append(src)

    # Meteo subsets
    # Read from toml file
    meteo_path = cosmos.config.meteo_database.path
    file_name = os.path.join(meteo_path,
                            "meteo_subsets.toml")
    toml_dict = toml.load(file_name)
    
    parameters = ["wind","barometric_pressure","precipitation"]
    
    has_source_list = []
    for toml_meteo in toml_dict["meteo_subset"]:

        name       = toml_meteo['name']
        path       = os.path.join(meteo_path, name)
        srcname    = toml_meteo['source']
        # Look for matching source
        for src in cosmos.meteo_source:
            if srcname.lower() == src.name.lower():
                x_range = None
                y_range = None
                if "x_range" in toml_meteo:
                    x_range = toml_meteo['x_range']
                    y_range = toml_meteo['y_range']
                xystride = 1    
                tstride  = 1    
                if "xystride" in toml_meteo:
                    xystride = int(toml_meteo['xystride'])
                if "tstride" in toml_meteo:
                    tstride = int(toml_meteo['tstride'])
                subset = MeteoGrid(name=name,
                                   source=src,
                                   parameters=parameters,
                                   path=path,
                                   x_range=x_range,
                                   y_range=y_range,
                                   crs=src.crs,
                                   xystride=xystride,
                                   tstride=tstride)
                cosmos.meteo_subset.append(subset)
                break

    #  # Now get the other datasets (not mentioned in the subset toml file) 
    # data_names = []
    # data_list = fo.list_folders(os.path.join(meteo_path,"*"))
    # for data_path in data_list:
    #     data_names.append(os.path.basename(data_path))
     

def download_meteo():
    """Download meteo sources listed in meteo_subsets.toml using cht_meteo.
    """    
    # Loop through all available meteo subsets
    # Determine if the need to be downloaded
    # Get start and stop times for meteo data
    for meteo_subset in cosmos.meteo_subset:
        download = False
        t0      = datetime.datetime(2100,1,1,0,0,0)
        t1      = datetime.datetime(1970,1,1,0,0,0)
        for model in cosmos.scenario.model:
            if model.meteo_subset:
                if model.meteo_subset.name == meteo_subset.name:
                     download = True
#                         if model.flow:
                     t0 = min(t0, model.flow_start_time)
                     t1 = max(t1, model.flow_stop_time)
        if download:
            # Download the data
            cosmos.log("Downloading meteo data : " + meteo_subset.name)
            meteo_subset.download([t0, t1])



def collect_meteo():
    """Collect meteo from netcdf files.
    """    
    # Loop through all available meteo subsets
    # Determine if the need to be downloaded
    # Get start and stop times for meteo data

    track_file_list = []

    for meteo_subset in cosmos.meteo_subset:

        collect = False
        t0      = datetime.datetime(2100,1,1,0,0,0)
        t1      = datetime.datetime(1970,1,1,0,0,0)

        for model in cosmos.scenario.model:
            if model.meteo_subset:
                if model.meteo_subset.name == meteo_subset.name:
                     collect = True
#                         if model.flow:
                     t0 = min(t0, model.flow_start_time)
                     t1 = max(t1, model.flow_stop_time)

        if collect:

            # Collect the data from netcdf files    
            cosmos.log("Collecting meteo data : " + meteo_subset.name)
            meteo_subset.collect([t0, t1],
                                 xystride=meteo_subset.xystride,
                                 tstride=meteo_subset.tstride)

            if meteo_subset.last_analysis_time:

                cosmos.log("Last analysis time : " + meteo_subset.last_analysis_time.strftime("%Y%m%d_%H%M%S"))
                file_name = os.path.join(meteo_subset.path, meteo_subset.last_analysis_time.strftime("%Y%m%d_%Hz"), "coamps_used.txt")
                if os.path.exists(file_name):
                    cosmos.storm_flag = True
                    keepfile_name = os.path.join(cosmos.scenario.cycle_path, "keep.txt")
                    fid = open(keepfile_name, "w")  # Why is there no path here?
                    fid.write("Coamps data was used in this cycle so we want to keep it \n")
                    fid.close()
                else:
                    cosmos.storm_flag = False
                

                # Save csv with meteo sources for each time step
                csv_path = os.path.join(cosmos.scenario.cycle_path, "meteo_sources.csv")
                meteo_subset.meteo_source.to_csv(csv_path)
                cosmos.scenario.meteo_string = "_".join(meteo_subset.meteo_source.values[-1][0].split("_")[:-1])

            # Check if track files are available in any of the cycle folders

            # Get folder names of meteo cycles
            cycle_folders = fo.list_folders(os.path.join(meteo_subset.path, "*"))

            # Loop through folders and determine time of cycle
            for folder in cycle_folders:
                try:
                    t = datetime.datetime.strptime(os.path.basename(folder), "%Y%m%d_%Hz")
                    # Track start time needs to be after or at the start time of the scenario. Tracks starting after scenario cycle time should not be used.
                    if t >= t0 and t <= cosmos.cycle.replace(tzinfo=None):
                        # Check if track file is available
                        track_files = glob.glob(os.path.join(folder, "*.trk"))
                        if len(track_files)>0:
                            track_file_list.append(track_files[0])
                except:
                    print("Error in reading folder name")
                    pass

    # Cyclone track

    # Don't try to find it anymore!

#     if not cosmos.scenario.meteo_track and not cosmos.scenario.meteo_spiderweb:

#         # Track file not provided, so try to find it in the meteo data

#         # If only gridded data, try to extract the storm track
#         # Use only the first meteo_subset for now

#         for meteo_subset in cosmos.meteo_subset:
#             if meteo_subset.name == cosmos.scenario.meteo_dataset:
#                 break

#         cosmos.log("Finding storm tracks ...")
#         tracks = meteo_subset.find_cyclone_tracks(method="vorticity",
#                                                 pcyc=100000.0,
#                                                 vcyc=40.0,
#                                                 vmin=18.0,
#                                                 dt = 3)
#         # Filter cyclone based on TCvitals
#         # Use coordinates specified in meteo file to extract nearest track from gridded meteo data (if present)
#         if hasattr(cosmos.scenario, 'meteo_lon'): 
#             meteo_lon = cosmos.scenario.meteo_lon
#             meteo_lat = cosmos.scenario.meteo_lat
#         else:
#             meteo_lon = None
#             meteo_lat = None

#         tc = find_priorityTC(tracks, "priority_storm.txt", meteo_lon, meteo_lat)
# #        tc = tracks[0]

#         # Use the first track to make ensembles
#         tc.account_for_forward_speed()
#         tc.estimate_missing_values()
#         tc.include_rainfall = True

#     else:

    # Cyclone track

    filename = None
    cosmos.tropical_cyclone = None

    # Check if track was provided in the scenario file
    if cosmos.scenario.meteo_track is not None:
        cosmos.log("Using track file provided in scenario file")
        filename = os.path.join(cosmos.config.meteo_database.path, "tracks", cosmos.scenario.meteo_track + ".cyc")
        # Check here whether the file exists
        if not os.path.exists(filename):
            # Stop the run
            cosmos.stop("Track file not found: " + filename)

    if filename is None:
        # Track file not provided, so see if track_file_list is empty
        if len(track_file_list) > 0:
            filename = track_file_list
        else:   
            cosmos.log("No cyclone track found")
            return

    # filename can now be a list of track files, or the name of a single track file
    tc = TropicalCyclone(track_file=filename)
    tc.config["include_rainfall"] = True

    if cosmos.config.run.spw_wind_field == "parametric":
        # Use Holland (2010)
        tc.compute_wind_field()

    else:    
        # Use the meteo data
        for meteo_subset in cosmos.meteo_subset:
            if meteo_subset.name == cosmos.scenario.meteo_dataset:
                # Resample the track to the meteo time step
                dt = int((meteo_subset.time[1]-meteo_subset.time[0]).total_seconds()/3600)
                tc.track.resample(dt, method="spline")
                # Set spiderweb file name
                cosmos.scenario.meteo_spiderweb = meteo_subset.name + ".spw"
                # Get wind field from meteo data
                tc.get_wind_field_from_meteo_dataset(meteo_subset)
                break

    fo.mkdir(cosmos.scenario.cycle_track_spw_path)        
    spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path,
                           cosmos.scenario.meteo_spiderweb)
    
    tc.write_spiderweb(spwfile, format="ascii", include_rainfall=True)

    # Also save the track file
    cycfile = os.path.join(cosmos.scenario.cycle_track_spw_path, "track.cyc")
    tc.track.write(cycfile)
    # And the js file (to be uploaded to the webviewer)
    jsfile = os.path.join(cosmos.scenario.cycle_track_spw_path, "track.geojson.js")
    tc.track.to_gdf(filename=jsfile)

    cosmos.tropical_cyclone = tc


def write_meteo_input_files(model, prefix, tref, path=None):
    
    if not path:
        path = model.job_path

    time_range = [model.flow_start_time, model.flow_stop_time]
    
    header_comments = False
    if model.type.lower() == "delft3dfm":
        header_comments = True
        
    # Check if the model uses 2d meteo forcing from weather model
    
    if model.meteo_subset:

        if model.crs.is_geographic:
        
            # Make a new subset that covers the domain of the model
            subset = model.meteo_subset.subset(xlim=model.xlim,
                                               ylim=model.ylim,
                                               time_range=time_range,
                                               crs=model.crs)
        
        else:
            dxy      = 5000.0
            x        = np.arange(model.xlim[0] - dxy, model.xlim[1] + dxy, dxy)
            y        = np.arange(model.ylim[0] - dxy, model.ylim[1] + dxy, dxy)
            subset   = model.meteo_subset.subset(x=x, y=y,
                                                 time_range=time_range,
                                                 crs=model.crs)
        
        # Check if meteo subset has data
        if subset:    
            if model.meteo_wind:                
                subset.write_to_delft3d(prefix,
                                        parameters=["wind"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)            
    
            if model.meteo_atmospheric_pressure:
                subset.write_to_delft3d(prefix,
                                        parameters=["barometric_pressure"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)
                            
            if model.meteo_precipitation:                
                subset.write_to_delft3d(prefix,
                                        parameters=["precipitation"],
                                        path=path,
                                        refdate=tref,
                                        time_range=time_range,
                                        header_comments=header_comments)
        
#     if model.meteo_spiderweb:
# #        model.domain.input.spwfile = model.meteo_spiderweb
# #        model.domain.input.baro    = 1
#         meteo_path = os.path.join(cosmos.config.main_path, "meteo", "spiderwebs")
#         src = os.path.join(meteo_path, model.meteo_spiderweb)
#         fo.copy_file(src, model.job_path)
    
# def track_to_spw():

#     # STILL TO UPDATE TO NEW CHT_CYCLONES !!!

#     from cht_cyclones.tropical_cyclone import TropicalCyclone
#     tc= TropicalCyclone()

#     if cosmos.scenario.meteo_spiderweb:
#         cyc = cosmos.scenario.meteo_spiderweb.split('.')[0] + ".cyc"
#     elif cosmos.scenario.meteo_track:
#         cyc = cosmos.scenario.meteo_track.split('.')[0] + ".cyc"
#         cosmos.scenario.meteo_track_ = cosmos.scenario.meteo_track.split('.')[0] + ".spw"

#     cycfile = os.path.join(cosmos.config.meteo_database.path,
#                     "tracks",
#                     cyc)
    
#     spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path,
#                         cosmos.scenario.meteo_spiderweb)
    
#     os.makedirs(os.path.dirname(spwfile), exist_ok=True)      
#     try:
#         tc.read_track(cycfile, 'ddb_cyc')
#         tc.include_rainfall = True
#         tc.to_spiderweb(spwfile, format_type='ascii')
#     except:
#         pass


# def get_cyclone_track():
#     pass



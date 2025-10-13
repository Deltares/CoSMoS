# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:28:58 2021

@author: ormondt
"""
import os
import glob
import datetime
import geopandas as gpd

from .cosmos_main import cosmos
import cht_utils.fileops as fo
from cht_cyclones import TropicalCyclone, jtwc
from cht_meteo import MeteoDatabase

def read_meteo_database():
    """Read meteo database."""    
    cosmos.meteo_database = MeteoDatabase()
    cosmos.meteo_database.path = cosmos.config.meteo_database.path
    cosmos.meteo_database.read_datasets()

def download_meteo():
    """Download meteo data."""    
    # Loop through all available meteo datasets
    # Determine if the need to be downloaded
    # Get start and stop times for meteo data
    for dataset_name, meteo_dataset in cosmos.meteo_database.dataset.items():
        download = False
        t0      = datetime.datetime(2100,1,1,0,0,0)
        t1      = datetime.datetime(1970,1,1,0,0,0)
        for model in cosmos.scenario.model:
            if model.meteo_dataset:
                if model.meteo_dataset.name == meteo_dataset.name:
                     download = True
                     t0 = min(t0, model.flow_start_time)
                     t1 = max(t1, model.flow_stop_time)
        if download:
            # Download the data
            cosmos.log("Downloading meteo data : " + meteo_dataset.name)
            meteo_dataset.download([t0, t1], storm_number=cosmos.scenario.storm_number)

    # Download cyclone tracks if needed
    if cosmos.scenario.cyclone_track_forecast_source is not None:
        if cosmos.scenario.cyclone_track_forecast_source.lower() == "jtwc":
            # Download JTWC tracks
            jtwc_path = os.path.join(cosmos.meteo_database.path, "tracks", "jtwc")
            jtwc.download(jtwc_path)

def collect_meteo():

    """Collect meteo from netcdf files."""    
    # Loop through all available meteo datasets
    # Determine if the need to be downloaded
    # Get start and stop times for meteo data

    tau = 0

    for dataset_name, meteo_dataset in cosmos.meteo_database.dataset.items():

        collect = False
        t0      = datetime.datetime(2100,1,1,0,0,0)
        t1      = datetime.datetime(1970,1,1,0,0,0)

        for model in cosmos.scenario.model:
            if model.meteo_dataset:
                if model.meteo_dataset.name == meteo_dataset.name:
                     collect = True
                     t0 = min(t0, model.flow_start_time)
                     t1 = max(t1, model.flow_stop_time)

        if collect:

            # Collect the data from netcdf files    
            cosmos.log("Collecting meteo data : " + meteo_dataset.name)
            if cosmos.config.run.collect_meteo_up_to_cycle:
                last_meteo_cycle = cosmos.cycle
            else:
                last_meteo_cycle = None
            meteo_dataset.collect([t0, t1], last_cycle=last_meteo_cycle)

            if meteo_dataset.last_analysis_time:

                cosmos.log("Last analysis time : " + meteo_dataset.last_analysis_time.strftime("%Y%m%d_%H%M%S"))

                # file_name = os.path.join(meteo_dataset.path, meteo_dataset.last_analysis_time.strftime("%Y%m%d_%Hz"), "coamps_used.txt")
                # if os.path.exists(file_name):
                #     cosmos.storm_flag = True
                #     keepfile_name = os.path.join(cosmos.scenario.cycle_path, "keep.txt")
                #     fid = open(keepfile_name, "w")  # Why is there no path here?
                #     fid.write("Coamps data was used in this cycle so we want to keep it \n")
                #     fid.close()
                # else:
                #     cosmos.storm_flag = False                

                # # Save csv with meteo sources for each time step
                # csv_path = os.path.join(cosmos.scenario.cycle_path, "meteo_sources.csv")

            if meteo_dataset.last_forecast_cycle_time:
                cosmos.log("Last forecast cycle time : " + meteo_dataset.last_forecast_cycle_time.strftime("%Y%m%d_%H%M%S"))
                # meteo_dataset.meteo_source.to_csv(csv_path)
                cstr = meteo_dataset.last_forecast_cycle_time.strftime("%Y%m%d_%Hz")
                cosmos.scenario.meteo_string = f"{ cstr } ({ meteo_dataset.name })"

            else:    
                cosmos.scenario.meteo_string = meteo_dataset.name + " (no cycle information available)"

            # # The next bit should be moved out of this loop 

            # # Check if track files are available in any of the cycle folders
            # cycle_folders = fo.list_folders(os.path.join(meteo_dataset.path, "*"))
            # track_file_list = []
            # tau = meteo_dataset.tau
            # # Loop through folders and determine time of cycle
            # for folder in cycle_folders:
            #     try:
            #         t = datetime.datetime.strptime(os.path.basename(folder), "%Y%m%d_%Hz")
            #         # For hindcasts, only use data up to the last cycle
            #         if last_meteo_cycle:
            #             if t > last_meteo_cycle.replace(tzinfo=None):
            #                 continue
            #         # Track start time needs to be after or at the start time of the scenario.
            #         if t >= t0:
            #             # Check if track file is available
            #             track_files = glob.glob(os.path.join(folder, "*.trk"))
            #             if len(track_files) > 0:
            #                 track_file_list.append(track_files[0])
            #                 storm_name = meteo_dataset.name
            #     except:
            #         print("Error in reading folder name")
            #         pass

    # Cyclone track
    # Don't try to find it anymore!

#     if not cosmos.scenario.meteo_track and not cosmos.scenario.meteo_spiderweb:

#         # Track file not provided, so try to find it in the meteo data

#         # If only gridded data, try to extract the storm track
#         # Use only the first meteo_dataset for now

#         for meteo_dataset in cosmos.meteo_dataset:
#             if meteo_dataset.name == cosmos.scenario.meteo_dataset:
#                 break

#         cosmos.log("Finding storm tracks ...")
#         tracks = meteo_dataset.find_cyclone_tracks(method="vorticity",
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

    # Now we collect the cyclone track file. There are three options:
    # 1. Track file provided in scenario file
    # 2. Track file provided by cyclone_track_forecast_source (e.g. JTWC)
    # 3. Track file found in meteo data folders

    # The track file will be copied to the cycle folder\\track folder and will be named storm.cyc.
    # The matching spiderweb file will be stored in the same folder and will be named storm.spw.

    cosmos.tropical_cyclone = None
    tc = None
    # track_file_name = None
    # storm_name = None

    if cosmos.scenario.meteo_track is not None:
    
        # 1. Track name provided in scenario file (cosmos.scenario.meteo_track is the name without path or extension!)
    
        cosmos.log("Using track file provided in scenario file")
        track_file_name = os.path.join(cosmos.config.meteo_database.path, "tracks", cosmos.scenario.meteo_track + ".cyc")
        storm_name = cosmos.scenario.meteo_track
        # Create a TropicalCyclone object
        tc = TropicalCyclone(track_file=track_file_name, name=storm_name)

    elif cosmos.scenario.cyclone_track_forecast_source is not None:

        # 2) Track provided by cyclone_track_forecast_source (e.g. JTWC)

        # Make sure that the area file is available and exists
        if cosmos.scenario.cyclone_track_forecast_area_file is not None:
            # Read the file (geojson) and get the Polygon geometry
            forecast_area = gpd.read_file(os.path.join(cosmos.config.path.main,
                                                       "configuration",
                                                       "areas",
                                                        cosmos.scenario.cyclone_track_forecast_area_file)).geometry.iloc[0]
        else:
            cosmos.stop("Track forecast area file (cyclone_track_forecast_area_file) not provided in scenario.toml !")

        if cosmos.scenario.cyclone_track_forecast_source.lower() == "jtwc":

            jtwc_path = os.path.join(cosmos.meteo_database.path, "tracks", "jtwc")
            t0 = cosmos.cycle.replace(tzinfo=None)
            t1 = cosmos.stop_time.replace(tzinfo=None)

            # Find the track
            track_file_name, storm_name = jtwc.find_jtwc_track_file(jtwc_path, t0, t1, forecast_area)

            if track_file_name is None:
                cosmos.log("No JTWC track found for this cycle")
                return

            # Make a TropicalCyclone object
            tc = TropicalCyclone(track_file=track_file_name, name=storm_name)

    else:

        # 3) Track may be found in meteo data folders. This is now the case for COAMPS-TC.

        for dataset_name, meteo_dataset in cosmos.meteo_database.dataset.items():

            collect = False

            for model in cosmos.scenario.model:
                if model.meteo_dataset:
                    if model.meteo_dataset.name == meteo_dataset.name:
                        collect = True

            if collect:

                # Check if track files are available in any of the cycle folders
                cycle_folders = fo.list_folders(os.path.join(meteo_dataset.path, "*"))
                track_file_list = []
                tau = meteo_dataset.tau
                # Loop through folders and determine time of cycle
                for folder in cycle_folders:
                    try:
                        t = datetime.datetime.strptime(os.path.basename(folder), "%Y%m%d_%Hz")
                        # For hindcasts, only use data up to the last cycle
                        if last_meteo_cycle:
                            if t > last_meteo_cycle.replace(tzinfo=None):
                                continue
                        # Track start time needs to be after or at the start time of the scenario.
                        if t >= t0:
                            # Check if track file is available
                            track_files = glob.glob(os.path.join(folder, "*.trk"))
                            if len(track_files) > 0:
                                track_file_list.append(track_files[0])
                                storm_name = meteo_dataset.name
                    except:
                        print("Error in reading folder name")
                        pass

                if len(track_file_list) == 0:
                    cosmos.log("No track files found for dataset: " + dataset_name)
                    return

                # Make a TC with list of track files
                tc = TropicalCyclone(track_file=track_file_list, name=storm_name)

    if tc is None:
        cosmos.log("No cyclone track found")
        return

    # There is a tropical cyclone track. Now determine how to get the wind field.
    # Two options:
    # 1. Parametric wind field (Holland 2010)
    # 2. Wind field from meteo data

    cosmos.scenario.meteo_spiderweb = "storm.spw"

    if cosmos.config.run.spw_wind_field == "parametric":
        # 1) Use Holland (2010)
        if not os.path.exists(os.path.join(cosmos.scenario.cycle_track_spw_path,
                            cosmos.scenario.meteo_spiderweb)):
            tc.compute_wind_field()

    else:

        # Use the meteo data
        for dataset_name, meteo_dataset in cosmos.meteo_database.dataset.items():
            if meteo_dataset.name == cosmos.scenario.meteo_dataset:

                if len(meteo_dataset.subset) > 0:
                    times = meteo_dataset.subset[0].ds.time.values
                else:
                    times = meteo_dataset.subset[0].ds.time.values

                dthours = 1
                tc.track.resample(dthours, method="spline")
                # Limit length of track to the meteo data (convert last time from np.datetime64 to datetime)
                tend = datetime.datetime.utcfromtimestamp(times[-1].astype(datetime.datetime) / 1e9)
                tc.track.shorten(tend=tend)
                # Get wind field from meteo data                
                tc.get_wind_field_from_meteo_dataset(meteo_dataset)
                break

    # We now have the wind field, so write the spiderweb file and cyc file in the cycle folder

    # Check if track path exists. If not, create it.
    if not os.path.exists(cosmos.scenario.cycle_track_spw_path):
        os.makedirs(cosmos.scenario.cycle_track_spw_path)

    spwfile = os.path.join(cosmos.scenario.cycle_track_spw_path,
                        cosmos.scenario.meteo_spiderweb)

    if not os.path.exists(spwfile):    
        # Only write spw file is it does not already exist
        tc.write_spiderweb(spwfile, format="ascii", include_rainfall=True)

    # Also save the track file
    cycfile = os.path.join(cosmos.scenario.cycle_track_spw_path, "storm.cyc")
    tc.track.write(cycfile)
    # And the js file (to be uploaded to the webviewer)
    jsfile = os.path.join(cosmos.scenario.cycle_track_spw_path, "track.geojson.js")
    tc.track.to_gdf(filename=jsfile)

    cosmos.tropical_cyclone = tc

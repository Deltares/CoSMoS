# Run SFINCS model ensemble (including some pre and post processing)

import os
import boto3
import datetime
import pandas as pd  
import numpy as np
import xarray as xr
import sys

import cht.misc.fileops as fo
from cht.misc.misc_tools import yaml2dict
from cht.misc.prob_maps import merge_nc_his
from cht.misc.prob_maps import merge_nc_map
from cht.tiling.tiling import make_floodmap_tiles
from cht.tiling.tiling import make_png_tiles
from cht.sfincs.sfincs import SFINCS
from cht.nesting.nest2 import nest2
#from cht.misc.argo import Argo

def read_ensemble_members():
    with open('ensemble_members.txt') as f:
        ensemble_members = f.readlines()
    ensemble_members = [x.strip() for x in ensemble_members]
    return ensemble_members

def get_s3_client(config):
    # Create an S3 client
    session = boto3.Session(
        aws_access_key_id=config["cloud"]["access_key"],
        aws_secret_access_key=config["cloud"]["secret_key"],
        region_name=config["cloud"]["region"]
    )
    return session.client('s3')

def prepare_ensemble(config):
    # In case of ensemble, make folders for each ensemble member and copy necessary scripts to these folders
    # Read in the list of ensemble members
    ensemble_members = read_ensemble_members()
    for member in ensemble_members:
        print('Making folder for ensemble member ' + member)
        # Make folder for ensemble member and copy all input files
        fo.mkdir(member)            
        fo.copy_file(os.path.join("base_input", "run_job_2.py"), member)
        fo.copy_file(os.path.join("base_input", "config.yml"), member)
        fo.copy_file(os.path.join("base_input", "ensemble_members.txt"), member)

def prepare_single(config, member=None):
    # Copying, nesting, spiderweb
    # We're already in the correct folder
    if config["run_mode"] == "cloud":
        # Initialize S3 client
        s3_client = get_s3_client(config)
        bucket_name = "cosmos-scenarios"

    if config["run_mode"] == "cloud":
        # Copy base input to member folder
        if config["ensemble"]:
            s3_key = config["scenario"] + "/" + "models" + "/" + config["model"] + "/" + "base_input" + "/"
        else:
            s3_key = config["scenario"] + "/" + "models" + "/" + config["model"] + "/"
        local_file_path = f'/input/'  # Replace with the local path where you want to save the file
        objects = s3_client.list_objects(Bucket=bucket_name, Prefix=s3_key)
        if "Contents" in objects:
            for object in objects['Contents']:
                key = object['Key']
                # Only download files in main folder, not in subfolders
                if key[-1] == "/":
                    continue
                if "/" in key.replace(s3_key, ""):
                    continue
                local_path = os.path.join(local_file_path, os.path.basename(key))
                print("Copying " + key + " to " + local_path) 
                s3_client.download_file(bucket_name, key, local_path)
    else:
        if config["ensemble"]:
            # Copy from input folder
            # We're already in the right member path
            fo.copy_file(os.path.join("..", "base_input", "*.*"), ".")

    # Copy spiderweb file
    if config["ensemble"]:
        print("Copying spiderweb file ...")
        if config["run_mode"] == "cloud":
            s3_key = config["scenario"] + "/" + "track_ensemble" + "/" + "spw" + "/ensemble" + member + ".spw"
            local_file_path = f'/input/sfincs.spw'  # Replace with the local path where you want to save the file
            # Download the file from S3
            try:
                s3_client.download_file(bucket_name, s3_key, local_file_path)
                print(f"File downloaded successfully to '{local_file_path}'")
            except Exception as e:
                print(f"Error: {e}")
        else:
            # Copy all spiderwebs to jobs folder
            fname0 = os.path.join(config["spw_path"], "ensemble" + member + ".spw")
            fo.copy_file(fname0, "sfincs.spw")

    # Read SFINCS model (necessary for nesting)
    sf = SFINCS("sfincs.inp")
    sf.name = config["model"]
    sf.type = "sfincs"
    sf.path = "."

    # Nesting
    if "flow_nested" in config:
        print("Nesting flow ...")
        # Get boundary conditions from overall model (Nesting 2)
        # Correct boundary water levels. Assuming that output from overall
        # model is in MSL !!!
        zcor = config["flow_nested"]["boundary_water_level_correction"] - config["vertical_reference_level_difference_with_msl"]
        # If cloud mode, copy boundary files from S3
        if config["run_mode"] == "cloud":
            file_name = config["flow_nested"]["overall_file"]    
            s3_key = config["scenario"] + "/" + "models" + "/" + config["flow_nested"]["overall_model"] + "/" + file_name
            local_file_path = f'/input/boundary'
            fo.mkdir(local_file_path)
            # Download the file from S3
            s3_client.download_file(bucket_name, s3_key, os.path.join(local_file_path, os.path.basename(s3_key)))
            # Change path in config
            config["flow_nested"]["overall_path"] = local_file_path   

        # Get boundary conditions from overall model (Nesting 2)
        if config["ensemble"]:
            nest2(config["flow_nested"]["overall_type"],
                sf,
                output_path=os.path.join(config["flow_nested"]["overall_path"], member),
                boundary_water_level_correction=zcor,
                option="flow",
                bc_path=".")
        else:
            # Deterministic    
            nest2(config["flow_nested"]["overall_type"],
                sf,
                output_path=config["flow_nested"]["overall_path"],
                boundary_water_level_correction=zcor,
                option="flow",
                bc_path=".")
        
    if "wave_nested" in config:
        print("Nesting wave ...")
        # Get boundary conditions from overall model (Nesting 2)
        if config["run_mode"] == "cloud":
            file_name = config["wave_nested"]["overall_file"]    
            s3_key = config["scenario"] + "/" + "models" + "/" + config["wave_nested"]["overall_model"] + "/" + file_name
            local_file_path = f'/input/boundary'
            fo.mkdir(local_file_path)
            # Download the file from S3
            s3_client.download_file(bucket_name, s3_key, os.path.join(local_file_path, os.path.basename(s3_key)))
            # Change path in config
            config["wave_nested"]["overall_path"] = local_file_path   

        # Get boundary conditions from overall model (Nesting 2)
        if config["ensemble"]:
            nest2(config["wave_nested"]["overall_type"],
                sf,
                output_path=os.path.join(config["wave_nested"]["overall_path"], member),
                option="wave",
                bc_path=".")
        else:
            # Deterministic    
            nest2(config["wave_nested"]["overall_type"],
                sf,
                output_path=config["wave_nested"]["overall_path"],
                option="wave",
                bc_path=".")

    # If SFINCS nested in Hurrywave for SNAPWAVE setup, separately run BEWARE nesting for LF waves
    if "bw_nested" in config:
        print("Nesting bw ...")
        if config["run_mode"] == "cloud":
            file_name = config["bw_nested"]["overall_file"]    
            s3_key = config["scenario"] + "/" + "models" + "/" + config["bw_nested"]["overall_model"] + "/" + file_name
            local_file_path = f'/input/boundary'
            fo.mkdir(local_file_path)
            # Download the file from S3
            s3_client.download_file(bucket_name, s3_key, os.path.join(local_file_path, os.path.basename(s3_key)))
            # Change path in config
            config["bw_nested"]["overall_path"] = local_file_path   
        # Get boundary conditions from overall model (Nesting 2)
        if config["ensemble"]:
            nest2(config["bw_nested"]["overall_type"],
                sf,
                output_path=os.path.join(config["wave_nested"]["overall_path"], member),
                option="wave",
                bc_path=".")
        else:
            # Deterministic    
            nest2(config["bw_nested"]["overall_type"],
                sf,
                output_path=config["bw_nested"]["overall_path"],
                option="wave",
                bc_path=".",
                detail_crs=config["bw_nested"]["detail_crs"],
                overall_crs=config["bw_nested"]["overall_crs"])
        sf.write_wavemaker_forcing_points()

def merge_ensemble(config):
    print("Merging ...")
    if config["run_mode"] == "cloud":
        folder_path = '/input'
        his_output_file_name = os.path.join("/output/sfincs_his.nc")
        map_output_file_name = os.path.join("/sfincs_map.nc")
    else:
        folder_path = './'
        his_output_file_name = "./output/sfincs_his.nc"
        map_output_file_name = "./sfincs_map.nc"
    output_path = './output'
    os.makedirs("output", exist_ok=True)

    # Read in the list of ensemble members
    ensemble_members = read_ensemble_members()
    # Merge output files
    his_files = []
    map_files = []
    for member in ensemble_members:
        os.makedirs(os.path.join(output_path, member), exist_ok=True)
        if os.path.exists(os.path.join(folder_path, member, "sfincs_his.nc")):
            his_files.append(os.path.join(folder_path, member, "sfincs_his.nc"))
            fo.copy_file(os.path.join(folder_path, member, "sfincs_his.nc"), os.path.join(output_path, member, "sfincs_his.nc"))
        map_files.append(os.path.join(folder_path, member, "sfincs_map.nc"))

    merge_nc_his(his_files, ["point_zs"], output_file_name=his_output_file_name)
    if "flood_map" in config:
        try:
            merge_nc_map(map_files, ["zsmax", "cumprcp"], output_file_name=map_output_file_name)
        except:
            print('Merging does not work for quadtree yet')
    # Copy restart files from the first ensemble member (restart files are the same for all members)
    fo.copy_file(os.path.join(folder_path, ensemble_members[0], 'sfincs.*.rst'), folder_path)    

def map_tiles(config):

    # Make flood map tiles
    if "flood_map" in config:

        # Make SFINCS object
        sf = SFINCS()

        print("Making flood map ...")

        flood_map_path = config["flood_map"]["png_path"]
        index_path     = config["flood_map"]["index_path"]
        topo_path      = config["flood_map"]["topo_path"]
        zsmax_path     = config["flood_map"]["zsmax_path"]
                
        if os.path.exists(index_path) and os.path.exists(topo_path):
            
            print("Making flood map tiles for model " + config["model"] + " ...")                

            # ... hour increments  
            dtinc = config["flood_map"]["interval"]

            # Wave map for the entire simulation
            dt1 = datetime.timedelta(hours=1)
            dt  = datetime.timedelta(hours=dtinc)
            t0  = config["flood_map"]["start_time"].replace(tzinfo=None)
            t1  = config["flood_map"]["stop_time"].replace(tzinfo=None)
                
            requested_times = pd.date_range(start=t0 + dt,
                                            end=t1,
                                            freq=str(dtinc) + "H").to_pydatetime().tolist()

            color_values = config["flood_map"]["color_map"]["contours"]

            pathstr = []
            for it, t in enumerate(requested_times):
                pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))

            zsmax_file = os.path.join(zsmax_path, "sfincs_map.nc")
            
            if config["ensemble"]:
                varname = "zsmax_90"
            else:
                varname = "zsmax"    

            try:
                # Inundation map over dt-hour increments                    
                for it, t in enumerate(requested_times):

                    zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
                                          time_range=[t - dt + dt1, t + dt1],
                                          varname=varname)
                    # Difference between MSL and NAVD88 (used in topo data)
                    zsmax += config["vertical_reference_level_difference_with_msl"]
                    zsmax = np.transpose(zsmax)

                    png_path = os.path.join(flood_map_path,
                                            config["scenario"],
                                            config["cycle"],
                                            config["flood_map"]["name"],
                                            pathstr[it])                                            

                    make_floodmap_tiles(zsmax, index_path, png_path, topo_path,
                                        color_values=color_values,
                                        zoom_range=[0, 13],
                                        zbmax=1.0,
                                        quiet=True)

                # Full simulation        
                zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
                                    time_range=[t0 + dt1, t1 + dt1],
                                    varname=varname)
                zsmax += config["vertical_reference_level_difference_with_msl"]
                zsmax = np.transpose(zsmax)

                png_path = os.path.join(flood_map_path,
                                        config["scenario"],
                                        config["cycle"],
                                        config["flood_map"]["name"],
                                        pathstr[-1]) 

                make_floodmap_tiles(zsmax, index_path, png_path, topo_path,
                                    color_values=color_values,
                                    zoom_range=[0, 13],
                                    zbmax=1.0,
                                    quiet=True)
            except Exception as e:
                print("An error occured while making flood map tiles: ". str(e))

    if "water_level_map" in config:

        # Make SFINCS object
        sf = SFINCS()
        
        # Make water level map tiles
        print("Making water level map tiles ...")

        water_level_map_path = config["water_level_map"]["png_path"]
        index_path           = config["water_level_map"]["index_path"]
        topo_path            = config["water_level_map"]["topo_path"]
        zsmax_path           = config["water_level_map"]["zsmax_path"]
        
        # Get the difference between MSL and local vertical reference level to correct the water level
        water_level_correction = config["vertical_reference_level_difference_with_msl"]
        zbmax = 0.0

        # NOTE all overland models get a boundary_water_level_correction
        # this causes an offset wrt the surge models
        # correct surge models as well to align plots:
        if water_level_correction == 0.0: # default value
            water_level_correction += 0.15
            zbmax = -1.0

        if os.path.exists(index_path) and os.path.exists(topo_path):

            print("Making water level map tiles for model " + config["model"] + " ...")

            # start and stop time
            t0  = config["water_level_map"]["start_time"].replace(tzinfo=None)
            t1  = config["water_level_map"]["stop_time"].replace(tzinfo=None)

            # ... hour increments  
            dtinc = config["water_level_map"]["interval"]

            # Compute interval in datetime format
            dt1 = datetime.timedelta(hours=1)
            dt  = datetime.timedelta(hours=dtinc)

            # Compute requested times
            requested_times = pd.date_range(start=t0 + dt,
                                            end=t1,
                                            freq=str(dtinc) + "H").to_pydatetime().tolist()
            
            pathstr = []
            for it, t in enumerate(requested_times):
                pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))            

            zsmax_file = os.path.join(zsmax_path, "sfincs_map.nc")
            
            if config["ensemble"]:
                varname = "zsmax_90"
            else:
                varname = "zsmax"

            try:
                color_values = config["water_level_map"]["color_map"]["contours"]

                # Water level map over dt-hour increments                    
                for it, t in enumerate(requested_times):

                    zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
                                          time_range=[t - dt + dt1, t + dt1],
                                          varname=varname)
                    zsmax += water_level_correction
                    zsmax = np.transpose(zsmax)

                    png_path = os.path.join(water_level_map_path,
                                            config["scenario"],
                                            config["cycle"],
                                            config["water_level_map"]["name"],
                                            pathstr[it]) 
                    
                    make_png_tiles(
                        valg=zsmax,
                        index_path=index_path,
                        png_path=png_path,
                        option="water_level",
                        zoom_range=[0,11],
                        topo_path=topo_path,
                        color_values=color_values,
                        zbmax=zbmax,
                        quiet=True,
                    ) 

                # Full simulation        
                zsmax = sf.read_zsmax(zsmax_file=zsmax_file, varname=varname)

                zsmax += water_level_correction
                zsmax = np.transpose(zsmax)

                png_path = os.path.join(water_level_map_path,
                                        config["scenario"],
                                        config["cycle"],
                                        config["water_level_map"]["name"],
                                        pathstr[-1]) 

                make_png_tiles(
                    valg=zsmax,
                    index_path=index_path,
                    png_path=png_path,
                    option="water_level",
                    zoom_range=[0,11],
                    topo_path=topo_path,
                    color_values=color_values,
                    zbmax=zbmax,
                    quiet=True,
                )
                            
            except Exception as e:
                print("An error occured while making flood map tiles: {}".format(str(e)))

    if "precipitation_map" in config:
            
        # Make SFINCS object
        sf = SFINCS()
        
        # Make precipitation map tiles
        print("Making precipitation map tiles ...")

        precipitation_map_path = config["precipitation_map"]["png_path"]
        index_path            = config["precipitation_map"]["index_path"]
        cumprcp_path          = config["precipitation_map"]["output_path"]
        
        if os.path.exists(index_path):

            print("Making precipitation map tiles for model " + config["model"] + " ...")

            t0  = config["precipitation_map"]["start_time"].replace(tzinfo=None)
            t1  = config["precipitation_map"]["stop_time"].replace(tzinfo=None)

            pathstr = []
            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))            

            cumprcp_file = os.path.join(cumprcp_path, "sfincs_map.nc")
            
            if config["ensemble"]:
                varname = "cumprcp_90"
            else:
                varname = "cumprcp"
            try:
                # Full simulation        
                # TODO fix this function in CHT, now it doesnt work for different varnames
                # cumprcp = sf.read_cumulative_precipitation(file_name=cumprcp_file)
                ds = xr.open_dataset(cumprcp_file)
                cumprcp = (ds[varname].isel(timemax=-1)-ds[varname].isel(timemax=0)).values
                cumprcp = np.transpose(cumprcp)

                png_path = os.path.join(precipitation_map_path,
                                        config["scenario"],
                                        config["cycle"],
                                        config["precipitation_map"]["name"],
                                        pathstr[-1]) 

                color_values = config["precipitation_map"]["color_map"]["contours"]

                # only show values above 1.0 mm
                cumprcp[np.where(cumprcp<1.0)] = np.nan

                make_png_tiles(
                    valg=cumprcp,
                    index_path=index_path,
                    png_path=png_path,
                    zoom_range=[0,10],
                    color_values=color_values,
                    quiet=True,
                )
                            
            except Exception as e:
                print("An error occured while making precipitation map tiles: {}".format(str(e)))

def clean_up(config):
    if config["ensemble"]:
        # Remove all ensemble members 
        # Read in the list of ensemble members
        with open('ensemble_members.txt') as f:
            ensemble_members = f.readlines()
        ensemble_members = [x.strip() for x in ensemble_members]
        if config["run_mode"] == "cloud":
            s3_client = get_s3_client(config)
            bucket_name = "cosmos-scenarios"
            config["scenario"] + "/" + config["model"]
            for member in ensemble_members:
                s3key = config["scenario"] + "/" + "models" + "/" + config["model"] + "/" + member
                # Delete folder from S3
                objects = s3_client.list_objects(Bucket=bucket_name, Prefix=s3key)
                for object in objects['Contents']:
                    s3_client.delete_object(Bucket=bucket_name, Key=object['Key'])
        else:
            for member in ensemble_members:
                try:
                    fo.rmdir(member)
                    print("Directory has been removed successfully : " + member)
                except OSError as error:
                    print(error)
                    print("Directory can not be removed : " + member)

# SFINCS job script

member_name = None
option = sys.argv[1]

print("Running run_job.py")
print("Option: " + option)

# Read config file (config.yml)
config = yaml2dict("config.yml")

# Check if member is specified
member = None
if len(sys.argv) == 3:
    member = sys.argv[2]
    print("Member: " + member)

if option == "prepare_ensemble":
    # Prepare folders
    prepare_ensemble(config)

elif option == "simulate":
    # Never called in cloud mode
    if config["ensemble"]:
        # Read in the list of ensemble members
        ensemble_members = read_ensemble_members()
        # Loop through members
        curdir = os.getcwd()
        for member in ensemble_members:
            print('Running ensemble member ' + member)
            os.chdir(member)
            # Run the SFINCS model
            prepare_single(config, member=member)
            os.system("call run_sfincs.bat\n")
            os.chdir(curdir)
    else:
        prepare_single(config)
        os.system("call run_sfincs.bat\n")

elif option == "prepare_single":
    # Only occurs in cloud mode (running single is done in workflow)
    prepare_single(config, member=member)

# elif option == "simulate_single":
#     # Only called in cloud mode (should move this back to container?)
#     # Kick off cosmos-sfincs workflow (which runs this script with prepare_single, and then runs the sfincs docker)
#     # So effectively, it does the same as run consecutively running prepare_single and run_single
#     subfolder = config["scenario"] + "/" + "models" + "/" + config["model"]
#     if config["ensemble"]:
#         subfolder += "/" + member
#     print("Submitting member in " + subfolder)    
#     w = Argo(config["cloud"]["host"], "sfincs-workflow")
#     w.submit_job(bucket_name="cosmos-scenarios",
#                  subfolder=subfolder,
#                  member=member)

elif option == "merge_ensemble":
    # Merge his and map files from ensemble members
    merge_ensemble(config)

elif option == "map_tiles":
    # Make flood map tiles
    map_tiles(config)

elif option == "clean_up":
    # Remove all ensemble members
    clean_up(config)

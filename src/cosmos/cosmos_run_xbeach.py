# Run XBeach model (including some pre and post processing)

import os
import pandas as pd  
import numpy as np
import sys
import boto3
import datetime

import cht.misc.fileops as fo
from cht.misc.misc_tools import yaml2dict
from cht.tiling.tiling import make_floodmap_tiles
from cht.tiling.tiling import make_png_tiles
from cht.xbeach.xbeach import XBeach
from cht.nesting.nest2 import nest2
#from cht.misc.argo import Argo

def get_s3_client(config):
    # Create an S3 client
    session = boto3.Session(
        aws_access_key_id=config["cloud"]["access_key"],
        aws_secret_access_key=config["cloud"]["secret_key"],
        region_name=config["cloud"]["region"]
    )
    return session.client('s3')

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

    # Read XBeach model (necessary for nesting)
    xb = XBeach()
    xb.name = config["model"]
    xb.type = "xbeach"
    xb.path = "."

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
                xb,
                output_path=config["flow_nested"]["overall_path"],
                boundary_water_level_correction=zcor,
                option="flow",
                bc_path=".",
                ensemble_member_index=int(member))
        else:
            # Deterministic    
            nest2(config["flow_nested"]["overall_type"],
                xb,
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
            config["flow_nested"]["overall_path"] = local_file_path   

        # Get boundary conditions from overall model (Nesting 2)
        if config["ensemble"]:
            nest2(config["wave_nested"]["overall_type"],
                XBeach,
                output_path=config["wave_nested"]["overall_path"],
                option="timeseries",
                bc_path=".",
                ensemble_member_index=int(member))
        else:
            # Deterministic    
            nest2(config["wave_nested"]["overall_type"],
                xb,
                output_path=config["wave_nested"]["overall_path"],
                option="timeseries",
                bc_path=".")


def map_tiles(config):

    # Make flood map tiles
    if "flood_map" in config:

        # Make SFINCS object
        xb = XBeach()

        print("Making maps ...")

        index_path     = config["flood_map"]["index_path"]  
        sedero_path     = config["flood_map"]["sedero_path"]
        zb0_path        = config["flood_map"]["zb0_path"]
        zbend_path      = config["flood_map"]["zbend_path"]

                
        # if os.path.exists(index_path):
            
        #     print("Making flood map tiles for model " + config["model"] + " ...")                

        #     # 24 hour increments  
        #     dtinc = 24

        #     # Wave map for the entire simulation
        #     dt1 = datetime.timedelta(hours=1)
        #     dt  = datetime.timedelta(hours=dtinc)
        #     t0  = config["flood_map"]["start_time"].replace(tzinfo=None)
        #     t1  = config["flood_map"]["stop_time"].replace(tzinfo=None)
                
        #     requested_times = pd.date_range(start=t0 + dt,
        #                                     end=t1,
        #                                     freq=str(dtinc) + "H").to_pydatetime().tolist()

        #     color_values = config["flood_map"]["color_map"]["contours"]

        #     pathstr = []
        #     for it, t in enumerate(requested_times):
        #         pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))

        #     pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))

        #     #zsmax_file = "/input/sfincs_map.nc"
        #     zsmax_file = os.path.join(zsmax_path,
        #                               "sfincs_map.nc")
            
        #     if config["ensemble"]:
        #         varname = "zsmax_90"
        #     else:
        #         varname = "zsmax"    

        #     try:

        #         # Inundation map over dt-hour increments                    
        #         for it, t in enumerate(requested_times):

        #             zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
        #                                   time_range=[t - dt + dt1, t + dt1],
        #                                   varname=varname)
        #             # Difference between MSL and NAVD88 (used in topo data)
        #             zsmax += config["vertical_reference_level_difference_with_msl"]
        #             zsmax = np.transpose(zsmax)

        #             png_path = os.path.join(flood_map_path,
        #                                     config["scenario"],
        #                                     config["cycle"],
        #                                     config["flood_map"]["name"],
        #                                     pathstr[it])                                            

        #             make_floodmap_tiles(zsmax, index_path, png_path, topo_path,
        #                                 color_values=color_values,
        #                                 zoom_range=[0, 13],
        #                                 zbmax=1.0,
        #                                 quiet=True)

        #         # Full simulation        
        #         zsmax = sf.read_zsmax(zsmax_file=zsmax_file,
        #                             time_range=[t0 + dt1, t1 + dt1],
        #                             varname=varname)
        #         zsmax += config["vertical_reference_level_difference_with_msl"]
        #         zsmax = np.transpose(zsmax)

        #         png_path = os.path.join(flood_map_path,
        #                                 config["scenario"],
        #                                 config["cycle"],
        #                                 config["flood_map"]["name"],
        #                                 pathstr[-1]) 

        #         make_floodmap_tiles(zsmax, index_path, png_path, topo_path,
        #                             color_values=color_values,
        #                             zoom_range=[0, 13],
        #                             zbmax=1.0,
        #                             quiet=True)
            # except:
            #     print("An error occured while making flood map tiles")

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
            # Run the XBeach model
            prepare_single(config, member=member)
            os.system("call run_xbeach.bat\n")
            os.chdir(curdir)
    else:
        prepare_single(config)
        os.system("call run_xbeach.bat\n")

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

# Run HurryWave model (including some pre and post processing)

import os
import pandas as pd  
import numpy as np
import sys
import boto3
import datetime
import platform

#from cht_utils.argo import Argo
import cht_utils.fileops as fo
from cht_utils.misc_tools import yaml2dict
from cht_utils.prob_maps import merge_nc_his
from cht_utils.prob_maps import merge_nc_map
from cht_tiling.tiling import make_png_tiles
from cht_hurrywave.hurrywave import HurryWave
from cht_nesting import nest2

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
            local_file_path = f'/input/hurrywave.spw'  # Replace with the local path where you want to save the file
            # Download the file from S3
            try:
                s3_client.download_file(bucket_name, s3_key, local_file_path)
                print(f"File downloaded successfully to '{local_file_path}'")
            except Exception as e:
                print(f"Error: {e}")
        else:
            # Copy all spiderwebs to jobs folder
            fname0 = os.path.join(config["spw_path"], "ensemble" + member + ".spw")
            fo.copy_file(fname0, "hurrywave.spw")

    # Read HurryWave model (necessary for nesting)
    hw = HurryWave(load=True)
    hw.name = config["model"]
    hw.type = "hurrywave"
    hw.path = "."

    # Nesting
    if "wave_nested" in config:
        print("Nesting wave ...")
        # Get boundary conditions from overall model (Nesting 2)
        # If cloud mode, copy boundary files from S3
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
                hw,
                output_path=os.path.join(config["wave_nested"]["overall_path"], member),
                bc_path=".")
        else:
            # Deterministic    
            nest2(config["wave_nested"]["overall_type"],
                hw,
                output_path=config["wave_nested"]["overall_path"],
                bc_path=".")
        

def merge_ensemble(config):
    print("Merging ...")
    if config["run_mode"] == "cloud":
        folder_path = '/input'
        his_output_file_name = os.path.join("/output/hurrywave_his.nc")
#        map_output_file_name = os.path.join("/hurrywave_map.nc")
    else:
        folder_path = './'
        his_output_file_name = "./output/hurrywave_his.nc"
        map_output_file_name = "./hurrywave_map.nc"
    output_path = './output'
    os.makedirs("output", exist_ok=True)

    # Read in the list of ensemble members
    ensemble_members = read_ensemble_members()
    # Merge output files
    his_files = []
    map_files = []
    for member in ensemble_members:
        os.makedirs(os.path.join(output_path, member), exist_ok=True)
        if os.path.exists(os.path.join(folder_path, member, "hurrywave_his.nc")):
            his_files.append(os.path.join(folder_path, member, "hurrywave_his.nc"))
            fo.copy_file(os.path.join(folder_path, member, "hurrywave_his.nc"), os.path.join(output_path, member, "hurrywave_his.nc"))
        if os.path.exists(os.path.join(folder_path, member, "hurrywave_sp2.nc")):
            fo.copy_file(os.path.join(folder_path, member, "hurrywave_sp2.nc"), os.path.join(output_path, member, "hurrywave_sp2.nc"))
        map_files.append(os.path.join(folder_path, member, "hurrywave_map.nc"))

    merge_nc_his(his_files, ["point_hm0", "point_tp"], output_file_name=his_output_file_name)
    if "hm0_map" in config:
        merge_nc_map(map_files, ["hm0max"], output_file_name=map_output_file_name)
    # Copy restart files from the first ensemble member (restart files are the same for all members)
    fo.copy_file(os.path.join(folder_path, ensemble_members[0], 'hurrywave.*.rst'), folder_path)    

def map_tiles(config):

    # Make flood map tiles
    if "hm0_map" in config:

        # Make HW object
        hw = HurryWave()

        print("Making Hm0 map ...")

        hm0_path       = config["hm0_map"]["png_path"]
        index_path     = config["hm0_map"]["index_path"]
        output_path    = config["hm0_map"]["output_path"]
                
        if os.path.exists(index_path):
            
            print("Making wave map tiles for model " + config["model"] + " ...")                

            # ... hour increments  
            dtinc = config["hm0_map"]["interval"]

            # Wave map for the entire simulation
            dt1 = datetime.timedelta(hours=1)
            dt  = datetime.timedelta(hours=dtinc)
            t0  = config["hm0_map"]["start_time"].replace(tzinfo=None)
            t1  = config["hm0_map"]["stop_time"].replace(tzinfo=None)
                
            requested_times = pd.date_range(start=t0 + dt,
                                            end=t1,
                                            freq=str(dtinc) + "H").to_pydatetime().tolist()

            color_values = config["hm0_map"]["color_map"]["contours"]

            pathstr = []
            for it, t in enumerate(requested_times):
                pathstr.append((t - dt).strftime("%Y%m%d_%HZ") + "_" + (t).strftime("%Y%m%d_%HZ"))
            pathstr.append("combined_" + (t0).strftime("%Y%m%d_%HZ") + "_" + (t1).strftime("%Y%m%d_%HZ"))

            hm0max_file = os.path.join(output_path, "hurrywave_map.nc")
            
            if config["ensemble"]:
                varname = "hm0max_90"
            else:
                varname = "hm0max"    

            try:
                # Wave map over dt-hour increments                    
                for it, t in enumerate(requested_times):

                    hm0max = hw.read_hm0max(time_range=[t - dt + dt1, t + dt1],
                                            hm0max_file=hm0max_file,
                                            parameter=varname)                    
                    hm0max = np.transpose(hm0max)

                    png_path = os.path.join(hm0_path,
                                            config["scenario"],
                                            config["cycle"],
                                            config["hm0_map"]["name"],
                                            pathstr[it])                                            

                    make_png_tiles(hm0max, index_path, png_path,
                                   color_values=color_values,
                                   zoom_range=[0, 13],
                                   zbmax=1.0,
                                   quiet=True)

                # Full simulation        
                hm0max = hw.read_hm0max(time_range=[t0 + dt1, t1 + dt1],
                                        hm0max_file=hm0max_file,
                                        parameter=varname)                    
                hm0max = np.transpose(hm0max)

                png_path = os.path.join(hm0_path,
                                        config["scenario"],
                                        config["cycle"],
                                        config["hm0_map"]["name"],
                                        pathstr[-1]) 

                make_png_tiles(hm0max, index_path, png_path,
                                color_values=color_values,
                                zoom_range=[0, 13],
                                zbmax=1.0,
                                quiet=True)

            except Exception as e:
                print("An error occured while making wave map tiles: {}".format(str(e)))

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
    # Make run string (platform dependent)
    if platform.system() == "Windows":
        run_string = "call run_simulation.bat"
    else:
        run_string = "source ./run_simulation.sh"
    if config["ensemble"]:
        # Read in the list of ensemble members
        ensemble_members = read_ensemble_members()
        # Loop through members
        curdir = os.getcwd()
        for member in ensemble_members:
            print('Running ensemble member ' + member)
            os.chdir(member)
            # Run the Hurrywave model
            prepare_single(config, member=member)
            os.system(run_string)
            os.chdir(curdir)
    else:
        prepare_single(config)
        os.system(run_string)

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
    # Make map tiles
    map_tiles(config)

elif option == "clean_up":
    # Remove all ensemble members
    clean_up(config)

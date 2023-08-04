# Run SFINCS model ensemble (including some pre and post processing)

import os
import pandas as pd  
import numpy as np
import sys
import boto3

from cht.misc.misc_tools import yaml2dict
import cht.misc.fileops as fo
import cht.misc.prob_maps as pm
from cht.misc.prob_maps import merge_nc_his
from cht.misc.prob_maps import merge_nc_map
from cht.tiling.tiling import make_floodmap_tiles
import datetime
#from cht.sfincs.sfincs import SFINCS

#sf = SFINCS()

def find_subfolders(root_folder):
    subfolders = []
    for root, dirs, files in os.walk(root_folder):
        for dir_name in dirs:
            subfolder_path = os.path.join(root, dir_name)
            subfolders.append(subfolder_path)
    return subfolders

def prepare_ensemble(config):
    # In case of ensemble, make folders for each ensemble member and copy inputs to these folders
    if config["ensemble"]:
        # Read in the list of ensemble members
        with open('ensemble_members.txt') as f:
            ensemble_members = f.readlines()
        ensemble_members = [x.strip() for x in ensemble_members]
        for member in ensemble_members:
            print('Making folder for ensemble member ' + member)
            # Make folder for ensemble member and copy all input files
            fo.mkdir(member)
            # if config["run_mode"] != "cloud":
            #     # If not cloud mode, copy all input files
            #     # If cloud mode, the input files will be copied in the workflow
            #     # TODO: check if this is still needed in the cloud
            fo.copy_file("*.*", member)
    else:
        # Nothing to do here (all the inputs are already in the right folder)
        pass

def simulate_ensemble(config):
    # Never called in cloud mode
    # Read in the list of ensemble members
    with open('ensemble_members.txt') as f:
        ensemble_members = f.readlines()
    ensemble_members = [x.strip() for x in ensemble_members]
    # Loop through members
    curdir = os.getcwd()
    for member in ensemble_members:
        print('Running ensemble member ' + member)
        # Make folder for ensemble member and copy all input files
        os.chdir(member)
        # Run the SFINCS model
        simulate_single(config, member=member)
        os.chdir(curdir)

    # # Copy restart files from the first ensemble member (restart files are the same for all members)
    # fo.copy_file(ensemble_members[0] + '/sfincs.*.rst', './')    
    #     # os.chdir(member)
    #     # simulate_single(config, member=member)
    #     # os.chdir(curdir)

def simulate_single(config, member=None):

    # We're already in the correct folder

    # Nesting
    print("Nesting ...")

    # Spiderweb file
    print("Copying spiderweb file ...")
    if config["ensemble"]:
        # Copy spiderweb file
        if config["run_mode"] == "cloud":
            bucket_name = "cosmos-scenarios"
            s3_key = config["scenario"] + "/" + "track_ensemble" + "/" + "spw" + "/ensemble" + member + ".spw"
            local_file_path = f'/input/sfincs.spw'  # Replace with the local path where you want to save the file
            session = boto3.Session(
                aws_access_key_id=config["access_key"],
                aws_secret_access_key=config["secret_key"],
                region_name='eu-west-1'
            )
            # Create an S3 client
            s3 = session.client('s3')
            # Download the file from S3
            try:
                s3.download_file(bucket_name, s3_key, local_file_path)
                print(f"File downloaded successfully to '{local_file_path}'")
            except Exception as e:
                print(f"Error: {e}")
        else:
            # Copy all spiderwebs to jobs folder
            fname0 = os.path.join(config["spw_path"], "ensemble" + member + ".spw")
            fo.copy_file(fname0, "sfincs.spw")



    print("Running simulation ...")
    # And run the simulation
    if config["run_mode"] == "cloud":
        # Docker container is run in the workflow
        print("Docker container is run in the workflow")
#        os.system("docker run deltares/sfincs-cpu:latest\n")
        pass
    else:
        # Run the SFINCS model (this is only for windows)
        os.system("call run_sfincs.bat\n")

def merge_ensemble(config):
    print("Merging ...")

    folder_path = '/input'
    subfolders_list = find_subfolders(folder_path)

    file_list = []

    for subfolder in subfolders_list:
        file_list.append(os.path.join(folder_path, subfolder, "sfincs_his.nc"))

    # Make output folder_path
    os.mkdir("output")

    prcs= [0.05, 0.5, 0.95]
    vars= ["point_zs"]
    output_file_name = os.path.join("/output/sfincs_his.nc")
    pm.prob_floodmaps(file_list=file_list, variables=vars, prcs=prcs, delete = False, output_file_name=output_file_name)

    # Remove member folders
    for subfolder in subfolders_list:
        try:
            os.rmdir(subfolder)
            print("Directory has been removed successfully : " + subfolder)
        except OSError as error:
            print(error)
            print("Directory can not be removed : " + subfolder)


    # Merge output files
    his_files = []
    map_files = []
    for ensemble_member in ensemble_members:
        his_files.append(ensemble_member + '/sfincs_his.nc')
        map_files.append(ensemble_member + '/sfincs_map.nc')
    merge_nc_his(his_files, ["point_zs"], output_file_name="./sfincs_his.nc")
    if "flood_map" in config:
        merge_nc_map(map_files, ["zsmax"], output_file_name="./sfincs_map.nc")

    # Copy restart files from the first ensemble member (restart files are the same for all members)
    fo.copy_file(ensemble_members[0] + '/sfincs.*.rst', './')    


def map_tiles(config):

    # Make flood map tiles
    if "flood_map" in config:

        print("Make flood map")

        flood_map_path = config["flood_map"]["png_path"]
        index_path     = config["flood_map"]["index_path"]
        topo_path      = config["flood_map"]["topo_path"]
                
        if os.path.exists(index_path) and os.path.exists(topo_path):
            
            print("Making flood map tiles for model " + config["name"] + " ...")                

            # 24 hour increments  
            dtinc = 12

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

            zsmax_file = "./sfincs_map.nc"
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

                    make_floodmap_tiles(zsmax,
                                        index_path,
                                        png_path,
                                        topo_path,
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
            except:
                print("An error occured while making flood map tiles")

def clean_up(config):
    if config["ensemble"]:
        # Read in the list of ensemble members
        with open('ensemble_members.txt') as f:
            ensemble_members = f.readlines()
        ensemble_members = [x.strip() for x in ensemble_members]
        if config["run_mode"] == "cloud":
            session = boto3.Session(
                aws_access_key_id=config["access_key"],
                aws_secret_access_key=config["secret_key"],
                region_name='eu-west-1'
            )
            # Create an S3 client
            s3_client = session.client('s3')
            config["scenario"] + "/" + config["model"]
            for member in ensemble_members:
                s3key = config["scenario"] + "/" + config["model"] + "/" + member
                # Delete folder from S3
                objects = s3_client.list_objects(Bucket="cosmos-scenarios", Prefix=s3key)
                for object in objects['Contents']:
                    s3_client.delete_object(Bucket="cosmos-scenarios", Key=object['Key'])
        else:
            for member in ensemble_members:
                try:
                    os.rmdir(member)
                    print("Directory has been removed successfully : " + member)
                except OSError as error:
                    print(error)
                    print("Directory can not be removed : " + member)


member_name = None
option = sys.argv[1]

print("Running run_job.py")
print("Option: " + option)

# Read config file (config.yml)
config = yaml2dict("config.yml")

# Check if member is specified
if len(sys.argv) == 3:
    member = sys.argv[2]
    print("Member: " + member)

if option == "prepare_ensemble":
    # Prepare folders
    prepare_ensemble(config)
elif option == "simulate_ensemble":
    # Never called in cloud mode (in cloud mode, this is done in the workflow)
    simulate_ensemble(config)
elif option == "simulate_single": # includes nesting
    simulate_single(config, member=member)
elif option == "merge_ensemble":
    merge_ensemble(config)
elif option == "map_tiles":
    map_tiles(config)
elif option == "clean_up":
    clean_up(config)

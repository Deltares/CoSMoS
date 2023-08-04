# Run SFINCS model ensemble (including some pre and post processing)

import os
import sys
import boto3

from cht.misc.misc_tools import yaml2dict
import cht.misc.fileops as fo
import cht.misc.prob_maps as pm

def find_subfolders(root_folder):
    subfolders = []
    for root, dirs, files in os.walk(root_folder):
        for dir_name in dirs:
            subfolder_path = os.path.join(root, dir_name)
            subfolders.append(subfolder_path)
    return subfolders

def prepare(config):

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
    for member in ensemble_members:
        curdir = os.getcwd()
        os.chdir(member)
        simulate_single(config, member=member)
        os.chdir(curdir)

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

def merge(config):
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
            s3 = session.client('s3')
            config["scenario"] + "/" + config["model"]
            for member in ensemble_members:
                s3key = config["scenario"] + "/" + config["model"] + "/" + member + "/"
                # Delete folder from S3
                try:
                    s3.delete_object(Bucket="cosmos-scenarios", Key=s3key)
                    print(f"Folder deleted successfully : " + s3key)
                except Exception as e:
                    print(f"Error: {e}")
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

print("Running run_job_2.py")
print("Option: " + option)

# Read config file (config.yml)
config = yaml2dict("config.yml")


if len(sys.argv) == 3:
    member = sys.argv[2]
    print("Member: " + member)

if option == "prepare":
    # Prepare folders
    prepare(config)
elif option == "simulate_ensemble":
    # Never called in cloud mode
    simulate_ensemble(config)
elif option == "simulate_single":    
    simulate_single(config, member=member)
elif option == "merge":
    merge(config)
elif option == "clean_up":
    clean_up(config)


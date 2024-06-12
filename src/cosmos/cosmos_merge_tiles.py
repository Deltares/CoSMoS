# Merge model tiles from individual models into a shared directory.
# This is only used in the cloud

import os
import boto3
import tarfile
import shutil
from PIL import Image
import numpy as np

from cht.misc.misc_tools import yaml2dict

# Helper class for cloud functions, note this is a copy of necessary functionalities of cosmos_cloud
class Cloud:
    def __init__(self, config):  
        # Create a session using your AWS credentials (or configure it in other ways)
        session = boto3.Session(
            aws_access_key_id=config["cloud"]["access_key"],
            aws_secret_access_key=config["cloud"]["secret_key"],
            region_name=config["cloud"]["region"]
        )
        # Create an S3 client
        self.s3_client = session.client('s3')

    def list_folders(self, bucket_name, s3_folder):
        if s3_folder[-1] != "/":
             s3_folder = s3_folder + "/"
        folders = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        iterator = paginator.paginate(Bucket=bucket_name, Prefix=s3_folder, Delimiter='/')
        for page in iterator:
            for subfolder in page.get('CommonPrefixes', []):
                subfolder_name = subfolder['Prefix'].rstrip('/').split('/')[-1]
                folders.append(subfolder_name)
        return folders 

    def download_and_extract_tgz(self, bucket_name, s3_folder, local_folder):
        """
        Download and extract a .tgz file from S3.
        """
        local_tgz_path = os.path.join('/tmp', os.path.basename(s3_folder))
        
        # Download the .tgz file
        self.s3_client.download_file(bucket_name, s3_folder, local_tgz_path)
        
        # Extract the .tgz file
        with tarfile.open(local_tgz_path, "r:gz") as tar:
            tar.extractall(path=local_folder)
        
        # Clean up the downloaded .tgz file
        os.remove(local_tgz_path)

    def check_file_exists(self, bucket_name, s3_key):
        from botocore.exceptions import ClientError        
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise

# Helper functions, these should be put into cht_tiling?
def merge_images(image1_path, image2_path, output_path):
    """
    Merge two images by overlaying image2 on image1 and save the result.
    """
    with Image.open(image1_path) as img1, Image.open(image2_path) as img2:
        rgb1  = np.array(img1) # existing image
        rgb2 = np.array(img2)  # new image
        isum = np.sum(rgb1, axis=2) # sum of the existing image
        # replace the existing image with the new image where the existing image is zero
        rgb1[isum==0,:] = rgb2[isum==0,:] 
        im = Image.fromarray(rgb1)
        im.save(output_path)

def merge_model_tiles(model_tiles, merged_tiles):
    """
    Process tiles from multiple models and merge them if they already exist in the shared directory.
    """
    for root, _, files in os.walk(model_tiles):
        for file in files:
            if file.endswith('.png'):
                # Construct the full file paths
                src_path = os.path.join(root, file)
                relative_path = os.path.relpath(src_path, model_tiles)
                dest_path = os.path.join(merged_tiles, relative_path)

                # Ensure the destination directory exists
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # if file exist, merge, else move
                if os.path.exists(dest_path):
                    # Merge images if destination file already exists
                    merge_images(dest_path, src_path, dest_path)
                else:
                    # Move the file if it does not exist
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.move(src_path, dest_path)

def merge_tiles(config, quiet=True):
    """Merge tiles for a specific variable from individual models into a shared directory."""
    # Load the configuration file
    variable = config["variable"]["name"]
    scenario = config["cloud"]["scenario"]
    s3_bucket = config["cloud"]["s3_bucket"]

    # Initialize the cloud object
    cloud = Cloud(config)

    # tmp directories
    local_extract_path = './input/tmp'
    shared_directory = './output'

    # first make a list of all models within this scenario with the specific variable
    s3_keys = []
    for folder in cloud.list_folders(s3_bucket, "{}/models".format(scenario)):
        s3_key = "{}/models/".format(scenario) + folder + "/tiles/{}.tgz".format(variable)
        # check if the s3 key exists
        if cloud.check_file_exists(s3_bucket, s3_key):
            s3_keys.append(s3_key)

    # Ensure local directories exist and are empty
    shutil.rmtree(local_extract_path, ignore_errors=True)
    shutil.rmtree(shared_directory, ignore_errors=True)
    os.makedirs(local_extract_path, exist_ok=True)
    os.makedirs(shared_directory, exist_ok=True)

    # Download and extract each .tgz file
    for s3_key in s3_keys:
        # create a tmp directory for each model and download
        tmp_dir = os.path.join(local_extract_path, os.path.splitext(os.path.basename(s3_key))[0])
        cloud.download_and_extract_tgz(s3_bucket, s3_key, tmp_dir)
        if not quiet:
            print("Downloaded and extracted {}".format(s3_key))

        # Process the tiles (merge model tiles with existing tiles in shared directory)
        merge_model_tiles(tmp_dir, shared_directory)
        if not quiet:
            print("Processed tiles from {}".format(s3_key))

        # Clean up the extracted directory
        shutil.rmtree(tmp_dir)
    
    if not quiet:
        print("Merged tiles for variable {} in scenario {}".format(variable, scenario))

# Read config file (config.yml)
config = yaml2dict("config.yml")

print("Running merge_tiles.py")

merge_tiles(config, quiet=True)
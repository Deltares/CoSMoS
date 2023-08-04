from .cosmos import cosmos
import boto3
import os

import cht.misc.fileops as fo

class Cloud:
    # Helper class for cloud functions

    def __init__(self):  
        self.ready               = True
        # Create a session using your AWS credentials (or configure it in other ways)
        session = boto3.Session(
            aws_access_key_id=cosmos.config.cloud_config.access_key,
            aws_secret_access_key=cosmos.config.cloud_config.secret_key,
            region_name=cosmos.config.cloud_config.region
        )
        # Create an S3 client
        self.s3 = session.client('s3')

    def upload_folder(self, folder, bucket_name, subfolder):
        flist = fo.list_files(os.path.join(folder, "*"), full_path=True)
        for file in flist:
            s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
            self.s3.upload_file(file, bucket_name, s3_key)
            print("Uploaded " + os.path.basename(file))

    def upload_file(self, file, bucket_name, subfolder):
        s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
        # Upload the file to S3
        try:
            self.s3.upload_file(file, bucket_name, s3_key)
            print("Uploaded " + os.path.basename(file))
        except Exception as e:
            print("Error uploading " + os.path.basename(file))

    def download_file(self):
        pass

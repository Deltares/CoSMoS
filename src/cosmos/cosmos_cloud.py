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
        self.s3_client = session.client('s3')

    # def upload_folder(self, folder, bucket_name, subfolder):
    #     flist = fo.list_files(os.path.join(folder, "*"), full_path=True)
    #     for file in flist:
    #         s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
    #         self.s3.upload_file(file, bucket_name, s3_key)
    #         print("Uploaded " + os.path.basename(file))

    # def upload_file(self, file, bucket_name, subfolder):
    #     s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
    #     # Upload the file to S3
    #     try:
    #         self.s3.upload_file(file, bucket_name, s3_key)
    #         print("Uploaded " + os.path.basename(file))
    #     except Exception as e:
    #         print("Error uploading " + os.path.basename(file))

    # def download_file(self):
    #     pass

    def upload_file(self, bucket_name, file, s3_folder, quiet=True):
        s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
        self.s3_client.upload_file(file, bucket_name, s3_key)
        if not quiet:
            print("Uploaded " + os.path.basename(file))

    def download_file(self, bucket_name, s3_folder, file, local_folder, quiet=True):
        s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
        local_path = os.path.join(local_folder, os.path.basename(file))
        self.s3_client.download_file(bucket_name, s3_key, file, local_path)
        if not quiet:
            print("Downloaded " + os.path.basename(file))

    def delete_file(self, bucket_name, s3_folder, file, quiet=True):
        s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
        self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        if not quiet:
            print("Deleted " + os.path.basename(file))

    def make_folder(self, bucket_name, s3_folder, quiet=True):
        self.s3_client.put_objects(bBucket=bucket_name, Key=(s3_folder + '/'))
        if not quiet:
            print("Made folder: " + s3_folder)

    def upload_folder(self, bucket_name, local_folder, s3_folder, quiet=True):
        # Should do this recursively so that every subfolder is also uploaded
        flist = fo.list_files(os.path.join(local_folder, "*"), full_path=True)
        for file in flist:
            s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
            self.s3_client.upload_file(file, bucket_name, s3_key)
            if not quiet:
                print("Uploaded " + os.path.basename(file))

    def download_folder(self, bucket_name, s3_folder, local_folder, quiet=True):
        fo.mkdir(local_folder)
        objects = self.s3_client.list_objects(Bucket=bucket_name, Prefix=s3_folder)
        if "Contents" in objects:
            for object in objects['Contents']:
                s3_key = object['Key']
                local_path = os.path.join(local_folder, os.path.basename(s3_key))
                self.s3_client.download_file(bucket_name, s3_key, local_path)
                if not quiet:
                    print("Downloaded " + os.path.basename(s3_key))

    def delete_folder(self, bucket_name, folder):
        objects = self.s3_client.list_objects(Bucket=bucket_name, Prefix=folder)
        if "Contents" in objects:
            for object in objects['Contents']:
                self.s3_client.delete_object(Bucket=bucket_name, Key=object['Key'])

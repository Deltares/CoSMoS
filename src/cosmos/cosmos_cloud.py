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
        local_folder = local_folder.replace('\\\\','\\')
        local_folder = local_folder.replace('\\','/')
        # Recursively list all files
        flist = list_all_files(local_folder)
        for file in flist:
            file1 = file.replace('\\','/')
            file1 = file1.replace(local_folder,'')
            s3_key = s3_folder + file1
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
        objects = self.s3_client.list_objects(Bucket=bucket_name, Prefix=folder, Delimiter="/")
        if "Contents" in objects:
            for object in objects['Contents']:
                self.s3_client.delete_object(Bucket=bucket_name, Key=object['Key'])

    def list_folders(self, bucket_name, folder):
        folders = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder, Delimiter='/')
        for page in iterator:
            for subfolder in page.get('CommonPrefixes', []):
                subfolder_name = subfolder['Prefix'].rstrip('/').split('/')[-1]
                folders.append(subfolder_name)
        return folders 

def list_all_files(src):
    # Recursively list all files and folders in a folder
    import pathlib
    pth = pathlib.Path(src)
    pthlst = list(pth.rglob("*"))
    lst = []
    for f in pthlst:
        if f.is_file():
            lst.append(str(f))
    return lst        

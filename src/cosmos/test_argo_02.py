import boto3
import os
import cht.misc.fileops as fo

def upload_file(s3, file, bucket_name, subfolder):
    s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
    s3.upload_file(file, bucket_name, s3_key)
    print("Uploaded " + os.path.basename(file))

def upload_folder(s3, folder, bucket_name, subfolder):
    flist = fo.list_files(os.path.join(folder, "*"), full_path=True)
    for file in flist:
        s3_key = os.path.join(subfolder, os.path.basename(file)).replace('\\', '/')
        s3.upload_file(file, bucket_name, s3_key)
        print("Uploaded " + os.path.basename(file))

def download_file():
    pass

host       = "https://ae49d442936c347f8aed1336fd084d1e-1632268623.eu-west-1.elb.amazonaws.com:2746"
access_key = "AKIAQFTTKHPJJ34AN2EH"
secret_key = "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"
region     = "eu-west-1"

bucket_name = "cosmos-scenarios"

session = boto3.Session(
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=region
)

# Create an S3 client
s3 = session.client('s3')


# file_name = r"c:\work\cosmos\cosmos_clean_floris_02\tmp.bat"
# subfolder = "scripts"


# # Upload the file to S3
# try:
#     upload_file(s3,
#                 file_name,
#                 bucket_name,
#                 subfolder)
# except Exception as e:
#     print("failed")
#     pass

folder = r"c:\work\cosmos\cosmos_clean_floris_02\cosmos_runfolder\scenarios\hurricane_ian_03\20220928_00z\track_ensemble\spw"
try:
    upload_folder(s3,
                  folder,
                  bucket_name,
                  "spiderwebs")
except Exception as e:
    print("failed")
    pass

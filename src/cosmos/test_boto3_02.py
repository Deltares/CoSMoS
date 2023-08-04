import boto3
import os
import cht.misc.fileops as fo

def upload_file(s3_client, bucket_name, file, s3_folder, quiet=True):
    s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
    s3_client.upload_file(file, bucket_name, s3_key)
    if not quiet:
        print("Uploaded " + os.path.basename(file))

def download_file(s3_client, bucket_name, s3_folder, file, local_folder, quiet=True):
    s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
    local_path = os.path.join(local_folder, os.path.basename(file))
    s3_client.download_file(bucket_name, s3_key, file, local_path)
    if not quiet:
        print("Downloaded " + os.path.basename(file))

def delete_file(s3_client, bucket_name, s3_folder, file, quiet=True):
    s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
    s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
    if not quiet:
        print("Deleted " + os.path.basename(file))

def upload_folder(s3_client, bucket_name, local_folder, s3_folder, quiet=True):
    flist = fo.list_files(os.path.join(local_folder, "*"), full_path=True)
    for file in flist:
        s3_key = os.path.join(s3_folder, os.path.basename(file)).replace('\\', '/')
        s3_client.upload_file(file, bucket_name, s3_key)
        if not quiet:
            print("Uploaded " + os.path.basename(file))

def download_folder(s3_client, bucket_name, s3_folder, local_folder, quiet=True):
    os.mkdir(local_folder)
    objects = s3_client.list_objects(Bucket=bucket_name, Prefix=s3_folder)
    for object in objects['Contents']:
        s3_key = object['Key']
        local_path = os.path.join(local_folder, os.path.basename(s3_key))
        s3_client.download_file(bucket_name, s3_key, local_path)
        if not quiet:
            print("Downloaded " + os.path.basename(s3_key))

def delete_folder(s3_client, bucket_name, folder):
    objects = s3_client.list_objects(Bucket=bucket_name, Prefix=folder)
    for object in objects['Contents']:
        s3_client.delete_object(Bucket=bucket_name, Key=object['Key'])

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
s3_client = session.client('s3')


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

# folder = r"c:\work\cosmos\cosmos_clean_floris_02\cosmos_runfolder\scenarios\hurricane_ian_03\20220928_00z\track_ensemble\spw"
# try:
#     upload_folder(s3,
#                   folder,
#                   bucket_name,
#                   "spiderwebs")
# except Exception as e:
#     print("failed")
#     pass


# s3key = "hurricane_ian_04" + "/" + "sfincs_gom_500m_ensemble" + "/" + "00000" + "/" + "sfincs.bzs"
# # Delete folder from S3
# try:
#     xxx=s3.delete_object(Bucket="cosmos-scenarios", Key=s3key)
#     print(f"Folder deleted successfully : " + s3key)
# except Exception as e:
#     print(f"Error: {e}")

# s3key = "hurricane_ian_04" + "/" + "sfincs_gom_500m_ensemble" + "/" + "00000" + "/"
# s3key = "hurricane_ian_04" + "/" + "sfincs_gom_500m_ensemble" + "/"
# objects = s3.list_objects(Bucket="cosmos-scenarios", Prefix=s3key)
# for object in objects['Contents']:
#     print(object['Key'])
# #    s3_client.delete_object(Bucket='your-bucket', Key=object['Key'])
#     pass

# folder = "hurricane_ian_04" + "/" + "sfincs_gom_500m_ensemble" + "/" + "00000" + "/"
# delete_folder(s3_client, folder, "cosmos-scenarios")

bucket_name = "cosmos-scenarios"
local_folder = r'c:\work\cosmos\cosmos_clean_floris_02\cosmos_runfolder\scenarios\hurricane_ian_03\20220928_00z\track_ensemble\spw'
s3_folder = "spiderwebs_02"
upload_folder(s3_client, bucket_name, local_folder, s3_folder, quiet=True)

from .cosmos import cosmos
import boto3
import os

class Cloud:
    # Helper class for cloud functions

    def __init__(self):  
        self.ready               = True

    def upload_file(file, bucket_name, subfolder):
        s3_key = os.path.join(subfolder, file).replace('\\', '/')
 
        # Create a session using your AWS credentials (or configure it in other ways)
        session = boto3.Session(
            aws_access_key_id=cosmos.config.cloud_config.access_key,
            aws_secret_access_key=cosmos.config.cloud_config.secret_key,
            region_name=cosmos.config.cloud_config.region
        )

        # Create an S3 client
        s3 = session.client('s3')

        # Upload the file to S3
        try:
            s3.upload_file(os.path.join(cosmos.scenario.cycle_track_ensemble_spw_path, file), bucket_name, s3_key)
            cosmos.log(f"Spiderweb uploaded: {file}")
        except Exception as e:
            cosmos.log(f"Error: {e}")

    def download_file():
        pass
        
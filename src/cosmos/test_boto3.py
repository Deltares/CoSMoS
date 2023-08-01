import boto3

#Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id='AKIAQFTTKHPJJ34AN2EH',
aws_secret_access_key='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'
)

# region = "region=eu-west-1"

# #Creating S3 Resource From the Session.
# s3 = session.resource('s3')

# #s3 = boto3.client('s3')

# bucket = s3.Bucket('sfincs-data')
# xxx = bucket.objects.all()
# response = s3.list_buckets()

s3 = boto3.resource('s3')

for bucket in s3.buckets.all():
    print(bucket.name)
pass
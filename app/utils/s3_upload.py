import boto3
from config import AWSConfig
from werkzeug.utils import secure_filename

s3 = boto3.client(
    's3',
    aws_access_key_id=AWSConfig.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWSConfig.AWS_SECRET_ACCESS_KEY,
    region_name=AWSConfig.AWS_REGION
)

def upload_to_s3(file, folder):
    filename = secure_filename(file.filename)
    key = f"{folder}/{filename}"
    s3.upload_fileobj(
        file,
        AWSConfig.S3_BUCKET_NAME,
        key,
        ExtraArgs={'ACL': 'public-read'}
    )
    return f"https://{AWSConfig.S3_BUCKET_NAME}.s3.{AWSConfig.AWS_REGION}.amazonaws.com/{key}"
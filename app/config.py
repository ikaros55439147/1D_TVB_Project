import os
import boto3

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or \
        'postgresql://postgres:postgres@postgresdb:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "mailhog"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 1025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['cywong@example.com']
    POSTS_PER_PAGE = 3
    LANGUAGES = ['en', 'es', 'zh']


class AWSConfig:
    # # AWS RDS 配置
    # SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    
    # S3 配置
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION')
    AWS_REGION = os.getenv('AWS_REGION')
    S3_BUCKET = 'mytvbprojectbucket-oj'  # 替換為你的 Bucket 名稱
    AWS_REGION = 'ap-east-1'   
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
#     # 靜態文件 URL (通過 CloudFront)
#     STATIC_URL = 'https://d123.cloudfront.net'
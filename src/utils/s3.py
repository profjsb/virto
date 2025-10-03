import os

import boto3
from botocore.client import Config

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT_URL")
STORE_TO_S3 = os.environ.get("STORE_TO_S3", "false").lower() == "true"


def client():
    kw = {"region_name": S3_REGION}
    if S3_ENDPOINT:
        kw["endpoint_url"] = S3_ENDPOINT
        kw["config"] = Config(s3={"addressing_style": "virtual"})
    return boto3.client("s3", **kw)


def upload_file(local_path: str, key: str):
    if not STORE_TO_S3 or not S3_BUCKET:
        return None
    c = client()
    c.upload_file(local_path, S3_BUCKET, key)
    return {"bucket": S3_BUCKET, "key": key}


def presign(key: str, expires=3600):
    if not S3_BUCKET:
        return None
    c = client()
    return c.generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires
    )

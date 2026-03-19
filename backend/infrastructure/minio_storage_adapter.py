# Philippe Stepniewski
import os

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from backend.domain.ports.object_storage_handler import ObjectStorageHandler

BATCH_BUCKET = "batch-predictions"


class MinioStorageAdapter(ObjectStorageHandler):
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"],
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "minio_user"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "minio_password"),
        )

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=BATCH_BUCKET)
        except ClientError:
            self.s3.create_bucket(Bucket=BATCH_BUCKET)
            logger.info(f"Created bucket '{BATCH_BUCKET}'")

    def ensure_project_space(self, project_name: str) -> None:
        self._ensure_bucket()
        try:
            self.s3.put_object(Bucket=BATCH_BUCKET, Key=f"{project_name}/.keep", Body=b"")
        except ClientError as e:
            logger.warning(f"Could not create marker for '{project_name}': {e}")
        logger.info(f"Ensured project space for '{project_name}' in bucket '{BATCH_BUCKET}'")

    def remove_project_space(self, project_name: str) -> None:
        prefix = f"{project_name}/"
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BATCH_BUCKET, Prefix=prefix):
            objects = page.get("Contents", [])
            if objects:
                self.s3.delete_objects(
                    Bucket=BATCH_BUCKET,
                    Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
                )
        logger.info(f"Removed project space for '{project_name}' from bucket '{BATCH_BUCKET}'")

    def upload_file(self, project_name: str, remote_path: str, file_content: bytes) -> None:
        self._ensure_bucket()
        key = f"{project_name}/{remote_path}"
        self.s3.put_object(Bucket=BATCH_BUCKET, Key=key, Body=file_content)

    def download_file(self, project_name: str, remote_path: str) -> bytes:
        key = f"{project_name}/{remote_path}"
        response = self.s3.get_object(Bucket=BATCH_BUCKET, Key=key)
        return response["Body"].read()

    def list_files(self, project_name: str, prefix: str = "") -> list[str]:
        full_prefix = f"{project_name}/{prefix}"
        paginator = self.s3.get_paginator("list_objects_v2")
        files = []
        for page in paginator.paginate(Bucket=BATCH_BUCKET, Prefix=full_prefix):
            for obj in page.get("Contents", []):
                files.append(obj["Key"].removeprefix(f"{project_name}/"))
        return files

    def delete_file(self, project_name: str, remote_path: str) -> None:
        key = f"{project_name}/{remote_path}"
        self.s3.delete_object(Bucket=BATCH_BUCKET, Key=key)

    def file_exists(self, project_name: str, remote_path: str) -> bool:
        key = f"{project_name}/{remote_path}"
        try:
            self.s3.head_object(Bucket=BATCH_BUCKET, Key=key)
            return True
        except ClientError:
            return False

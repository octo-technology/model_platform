# Philippe Stepniewski
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from backend.infrastructure.minio_storage_adapter import BATCH_BUCKET, MinioStorageAdapter


@pytest.fixture
def adapter():
    with patch("backend.infrastructure.minio_storage_adapter.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        with patch.dict("os.environ", {"MLFLOW_S3_ENDPOINT_URL": "http://minio:9000"}):
            a = MinioStorageAdapter()
        yield a, mock_client


def test_ensure_project_space_creates_bucket(adapter):
    a, mock_client = adapter
    mock_client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    a.ensure_project_space("my-project")

    mock_client.create_bucket.assert_called_once_with(Bucket=BATCH_BUCKET)


def test_ensure_project_space_existing_bucket(adapter):
    a, mock_client = adapter

    a.ensure_project_space("my-project")

    mock_client.create_bucket.assert_not_called()


def test_remove_project_space_deletes_all_objects(adapter):
    a, mock_client = adapter
    paginator = MagicMock()
    mock_client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {"Contents": [{"Key": "my-project/.keep"}, {"Key": "my-project/data.csv"}]},
    ]

    a.remove_project_space("my-project")

    mock_client.delete_objects.assert_called_once_with(
        Bucket=BATCH_BUCKET,
        Delete={"Objects": [{"Key": "my-project/.keep"}, {"Key": "my-project/data.csv"}]},
    )


def test_remove_project_space_no_objects(adapter):
    a, mock_client = adapter
    paginator = MagicMock()
    mock_client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [{"Contents": []}]

    a.remove_project_space("my-project")

    mock_client.delete_objects.assert_not_called()

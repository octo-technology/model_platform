import os
import sys

import boto3
import mlflow
import pandas as pd
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    input_path = os.environ["INPUT_PATH"]
    output_path = os.environ["OUTPUT_PATH"]
    batch_bucket = os.environ.get("BATCH_BUCKET", "batch-predictions")
    s3_endpoint = os.environ["MLFLOW_S3_ENDPOINT_URL"]
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "minio_user")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "minio_password")

    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    logger.info(f"Downloading input file from {batch_bucket}/{input_path}")
    response = s3.get_object(Bucket=batch_bucket, Key=input_path)
    input_data = response["Body"].read()

    local_input = "/tmp/input.csv"
    with open(local_input, "wb") as f:
        f.write(input_data)

    logger.info("Loading model from /opt/mlflow/")
    model = mlflow.pyfunc.load_model("/opt/mlflow/")

    # Read expected column types from MLflow model signature and build dtype map for CSV parsing
    csv_dtype = None
    if model.metadata and model.metadata.signature:
        schema = model.metadata.signature.inputs
        type_mapping = {
            "double": "float64",
            "float": "float32",
            "long": "int64",
            "integer": "int32",
            "string": "object",
        }
        csv_dtype = {}
        for col in schema.inputs:
            mlflow_type = str(col.type)
            csv_dtype[col.name] = type_mapping.get(mlflow_type, "float64")
        logger.info(f"Using model signature to cast CSV columns: {csv_dtype}")

    logger.info("Running predictions by chunks of 1000 rows")
    all_predictions = []
    for chunk in pd.read_csv(local_input, chunksize=1000, dtype=csv_dtype):
        predictions = model.predict(chunk)
        if hasattr(predictions, "tolist"):
            predictions = predictions.tolist()
        all_predictions.extend(predictions)

    output_df = pd.DataFrame({"prediction": all_predictions})
    local_output = "/tmp/output.csv"
    output_df.to_csv(local_output, index=False)

    logger.info(f"Uploading results to {batch_bucket}/{output_path}")
    with open(local_output, "rb") as f:
        s3.put_object(Bucket=batch_bucket, Key=output_path, Body=f.read())

    logger.info(f"Batch prediction completed: {len(all_predictions)} predictions written")


if __name__ == "__main__":
    main()

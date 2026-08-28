# ghcr.io/mlflow/mlflow:v2.21.0 currently ships MLflow 3.12.0, so the pin was
# not doing its job. Pin the version we actually run.
FROM ghcr.io/mlflow/mlflow:v3.12.0

RUN pip install psycopg2-binary boto3

FROM python:3.10-slim
RUN pip install mlflow

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", ${MLFLOW_BACKEND_STORE_URI}, "--artifacts-destination", ${MLFLOW_ARTIFACTS_DESTINATION}]

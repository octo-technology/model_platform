FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

# Installe dependencies
RUN pip install --no-cache -r requirements.txt

# Commande pour lancer mlflow server
CMD sh -c "mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri ${MLFLOW_BACKEND_STORE_URI} --artifacts-destination ${MLFLOW_ARTIFACTS_DESTINATION}"

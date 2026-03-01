// Runtime configuration — this file is overwritten at container start
// by entrypoint.sh using environment variables.
// For local development, edit these values directly.
// For local dev: http://localhost:8000 — In prod K8s this file is overwritten by entrypoint.sh
window.API_BASE_URL           = 'http://localhost:8000';
window.MP_HOST_NAME           = 'model-platform.com';
window.MP_REGISTRY_PATH       = 'registry';
window.MLFLOW_S3_ENDPOINT_URL = '';


# Build an image that can serve mlflow models.
FROM python:3.8-slim

RUN apt-get -y update && apt-get install -y --no-install-recommends nginx

ENTRYPOINT ["python", "-c"]

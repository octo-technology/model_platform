FROM python:3.11-slim AS runtime

RUN apt-get update && \
    apt-get install -y docker.io && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./backend ./backend


RUN ls -R ./
RUN pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-root

FROM runtime AS final
WORKDIR /app

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "backend/__main__.py"]

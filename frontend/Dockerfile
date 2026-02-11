FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./pyproject.toml ./uv.lock ./

RUN mkdir -p ~/.streamlit
COPY ./frontend/config.toml ~/.streamlit/config.toml

RUN uv sync --frozen --no-install-project --group frontend

COPY ./frontend ./frontend


ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--server.enableWebsocketCompression=false"]

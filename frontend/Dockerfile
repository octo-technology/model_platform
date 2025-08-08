FROM python:3.11-slim AS runtime

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./frontend ./frontend
RUN mkdir -p ~/.streamlit
COPY ./frontend/config.toml ~/.streamlit/config.toml

RUN ls -R ./
RUN pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-root

FROM runtime AS final
WORKDIR /app
COPY ./.env ./


ENV PYTHONPATH=/app

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py",\
     "--server.port=8501",\
     "--server.address=0.0.0.0",\
     "--server.enableCORS=false",\
     "--server.enableXsrfProtection=false"]

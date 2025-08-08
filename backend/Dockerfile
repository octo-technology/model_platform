FROM python:3.11-slim AS runtime

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./backend ./backend

RUN ls -R ./
RUN pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-root

FROM runtime AS final
WORKDIR /app
COPY ./.env ./

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "backend/__main__.py"]

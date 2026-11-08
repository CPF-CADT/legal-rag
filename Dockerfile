FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app:/app/apps/core:/app/data-pipeline

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# The API image intentionally installs only its lightweight runtime dependencies.
# Pipeline, dense-retrieval, notebook, and test dependencies stay outside it.
COPY requirements-api.txt /tmp/requirements-api.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/requirements-api.txt \
    && rm -f /tmp/requirements-api.txt

COPY . .

RUN mkdir -p /app/data /app/apps/telegram_bot/logs

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

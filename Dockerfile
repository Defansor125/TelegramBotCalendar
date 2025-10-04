FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

COPY . .
CMD ["sh", "-c", "gunicorn app:app -k aiohttp.GunicornWebWorker --bind 0.0.0.0:${PORT:-8080}"]

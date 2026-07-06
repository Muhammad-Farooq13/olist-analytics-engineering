# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY dbt/ dbt/
COPY configs/ configs/
COPY dashboard/ dashboard/

# Ingest, load, and run the full dbt build (staging + marts + tests) at
# image build time, then export metrics/charts, so the container serves
# the dashboard immediately on `docker run` with no extra setup step.
RUN python -m src.ingest \
    && python -m src.load_raw \
    && dbt build --project-dir dbt --profiles-dir dbt \
    && python -m src.export_metrics

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]

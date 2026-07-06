.PHONY: install ingest load dbt-build build metrics dashboard test docker-build docker-run lint clean

install:
	pip install -r requirements.txt

ingest:
	python -m src.ingest

load: ingest
	python -m src.load_raw

dbt-build: load
	dbt build --project-dir dbt --profiles-dir dbt

build: dbt-build

metrics: build
	python -m src.export_metrics

dashboard:
	streamlit run dashboard/app.py

test:
	pytest --cov=src --cov-report=term-missing

docker-build:
	docker build -f docker/Dockerfile -t olist-analytics:latest .

docker-run:
	docker compose up --build

lint:
	python -m py_compile src/*.py tests/*.py

clean:
	rm -rf data/raw/*.csv artifacts/*.duckdb artifacts/*.json artifacts/*.png dbt/target dbt/logs .pytest_cache __pycache__ */__pycache__

.PHONY: dev test lint typecheck format db-up db-down db-init install

install:
	pip install -e ".[dev]"
	playwright install chromium

dev:
	uvicorn src.api.main:app --reload --port 8000

test:
	pytest -v --cov=src --cov-report=term-missing

test-unit:
	pytest -v -m "not integration" --cov=src

lint:
	ruff check src/ tests/

typecheck:
	mypy --strict src/

format:
	black --line-length=100 src/ tests/
	ruff check --fix src/ tests/

db-up:
	docker compose up -d db redis

db-down:
	docker compose down

db-init:
	python -m scripts.init_db

pipeline:
	python -m scripts.run_pipeline

check: lint typecheck test-unit

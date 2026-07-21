SHELL := /bin/bash

.PHONY: setup test quality readiness judge-demo lint typecheck coverage smoke run-api run-demo contracts deploy live-preflight submission preflight clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements-dev.txt
	cd contracts && npm ci

preflight:
	bash scripts/preflight.sh

lint:
	. .venv/bin/activate && ruff check apps scripts

typecheck:
	. .venv/bin/activate && mypy apps/api/app --ignore-missing-imports

test:
	. .venv/bin/activate && pytest -q
	cd contracts && npm test

coverage:
	. .venv/bin/activate && pytest --cov=apps.api.app --cov-report=term-missing --cov-fail-under=55

smoke:
	. .venv/bin/activate && python scripts/demo_smoke.py

quality: preflight lint typecheck test coverage smoke
	. .venv/bin/activate && python scripts/export_openapi.py

run-api:
	set -a; source .env; set +a; . .venv/bin/activate && uvicorn apps.api.app.main:app --reload --port 8000

run-demo:
	set -a; source .env; set +a; . .venv/bin/activate && streamlit run apps/demo/app.py

contracts:
	cd contracts && npm run compile

deploy:
	cd contracts && npm run deploy:sepolia

live-preflight:
	. .venv/bin/activate && python scripts/live_preflight.py

submission:
	. .venv/bin/activate && python scripts/generate_submission.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov **/__pycache__ contracts/artifacts contracts/cache artifacts/openapi.json

readiness:
	. .venv/bin/activate && python scripts/readiness.py

judge-demo:
	bash scripts/judge_demo.sh

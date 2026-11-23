PY      := venv/bin/python
PIP     := venv/bin/pip
COMPOSE := docker compose

.DEFAULT_GOAL := help

help: ## Zeige alle Ziele
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## venv + Abhängigkeiten (inkl. Dev)
	python3 -m venv venv
	$(PIP) install -e ".[dev]"

check: ## Django system check (Dev-Profil)
	$(PY) manage.py check

makemigrations: ## Migrationen erzeugen
	$(PY) manage.py makemigrations

migrate: ## Migrationen anwenden (DEV-Profil)
	$(PY) manage.py migrate

seed: ## Basisdaten anlegen (idempotent)
	$(PY) manage.py seed_basics

run: ## Dev-Server starten (localhost:8000)
	$(PY) manage.py runserver 0.0.0.0:8000

pytest: ## Tests (SQLite-Testprofil, lokal)
	FLOHMARKT_PROFILE=testing $(PY) -m pytest

pytest-cov: ## Tests mit Coverage
	FLOHMARKT_PROFILE=testing $(PY) -m pytest --cov=project --cov-report=term-missing

lint: ## Ruff (Check)
	$(PIP) show ruff >/dev/null 2>&1 || $(PIP) install ruff
	ruff check .
	ruff format --check . || true

format: ## Ruff Format + Fix
	ruff check --fix . && ruff format .

up: ## Docker Compose: Build + Start
	$(COMPOSE) up --build -d

down: ## Docker Compose: Stop
	$(COMPOSE) down

logs: ## Compose-Logs
	$(COMPOSE) logs -f --tail=100

pytest-docker: ## Tests gegen Postgres im Compose-Profil "tests"
	$(COMPOSE) --profile tests up -d db-tests
	@until $(COMPOSE) exec -T db-tests pg_isready -q -U flohmarkt -d flohmarkt_test 2>/dev/null; do sleep 1; done
	$(COMPOSE) --profile tests run --rm \
	  -e FLOHMARKT_PROFILE=testing \
	  -e DJANGO_SECRET_KEY=ci-test-key \
	  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
	  -e POSTGRES_HOST=db-tests \
	  -e POSTGRES_PORT=5432 \
	  -e POSTGRES_DB=flohmarkt_test \
	  -e POSTGRES_USER=flohmarkt \
	  -e POSTGRES_PASSWORD=test \
	  -v "$$PWD":/app \
	  app sh -c "python -m pip install --quiet 'pytest>=9.0,<10.0' 'pytest-django>=4.14,<5.0' && python -m pytest -q"

schema: ## OpenAPI-Schema erzeugen (docs/schema.json)
	$(PY) manage.py spectacular --file docs/schema.json

clean: ## Cache/Build-Artefakte entfernen (venv bleibt stehen)
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov dist build
	find . -name '__pycache__' -type d -not -path './venv/*' -print0 | xargs -0r rm -rf

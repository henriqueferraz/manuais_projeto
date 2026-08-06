.PHONY: help up down build migrate bootstrap shell test lint fmt ci collectstatic runserver golden golden-rag

help:
	@echo "Targets:"
	@echo "  make up           - sobe stack Docker (db, redis, web, worker, beat, flower, nginx)"
	@echo "  make down         - derruba stack"
	@echo "  make build        - rebuild imagens"
	@echo "  make migrate      - migrate no container web"
	@echo "  make bootstrap    - RBAC groups"
	@echo "  make runserver    - Django local (venv)"
	@echo "  make test         - pytest"
	@echo "  make golden       - regressão golden set de extração"
	@echo "  make golden-rag   - regressão golden set RAG"
	@echo "  make lint         - ruff + black --check + bandit"
	@echo "  make fmt          - black + ruff --fix"
	@echo "  make ci           - lint + test + golden + check migrations"

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec web python manage.py migrate

bootstrap:
	docker compose exec web python manage.py bootstrap_rbac

shell:
	docker compose exec web python manage.py shell

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

runserver:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.local \
		../.venv/bin/python manage.py runserver 0.0.0.0:8000

test:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/pytest -q

golden:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py run_golden_set

golden-rag:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py run_rag_golden_set

lint:
	.venv/bin/ruff check backend
	.venv/bin/black --check backend
	.venv/bin/bandit -q -r backend -x '*/tests/*,*/migrations/*'

fmt:
	.venv/bin/black backend
	.venv/bin/ruff check --fix backend

ci: lint test golden golden-rag
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py makemigrations --check --dry-run

.PHONY: help up down build migrate bootstrap shell test lint fmt ci collectstatic runserver golden golden-rag up-staging backup restore e2e

help:
	@echo "Targets:"
	@echo "  make up           - sobe stack Docker (db, redis, web, worker, beat, flower, nginx)"
	@echo "  make up-staging   - sobe stack com overlay staging (DEBUG=false)"
	@echo "  make down         - derruba stack"
	@echo "  make build        - rebuild imagens"
	@echo "  make migrate      - migrate no container web"
	@echo "  make bootstrap    - RBAC groups"
	@echo "  make runserver    - Django local (venv)"
	@echo "  make test         - pytest"
	@echo "  make e2e          - Playwright E2E (chromium; requer requirements/e2e.txt)"
	@echo "  make golden       - regressão golden set de extração"
	@echo "  make golden-rag   - regressão golden set RAG"
	@echo "  make lint         - ruff + black --check + bandit"
	@echo "  make fmt          - black + ruff --fix"
	@echo "  make ci           - lint + test + golden + check migrations"
	@echo "  make backup       - dump Postgres (RPO ≤24h — docs/deploy.md)"
	@echo "  make restore FILE=backups/....sql.gz"

up:
	docker compose up --build -d

up-staging:
	docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up --build -d

down:
	docker compose down

backup:
	bash scripts/backup_postgres.sh

restore:
	bash scripts/restore_postgres.sh "$(FILE)"

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

e2e:
	DJANGO_SETTINGS_MODULE=config.settings.e2e \
	DJANGO_ALLOW_ASYNC_UNSAFE=true \
		.venv/bin/pytest e2e -q --no-cov --browser chromium

golden:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py run_golden_set

golden-rag:
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py run_rag_golden_set

lint:
	.venv/bin/ruff check backend
	.venv/bin/black --check backend
	.venv/bin/bandit -q -r backend -x '*/tests/*,*/migrations/*,*/scripts_beta_s001.py'

fmt:
	.venv/bin/black backend
	.venv/bin/ruff check --fix backend

ci: lint test golden golden-rag
	cd backend && DJANGO_SETTINGS_MODULE=config.settings.test \
		../.venv/bin/python manage.py makemigrations --check --dry-run

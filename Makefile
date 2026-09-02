SHELL := /bin/bash

ENV_FILE := .env
PYTHON := $(HOME)/.pyenv/versions/3.11.11/bin/python
VENV_PYTHON := backend/.venv/bin/python
VENV_PIP := backend/.venv/bin/pip

.PHONY: install db-up db-down migrate backend frontend test test-integration lint typecheck build stop reset

install:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	$(PYTHON) -m venv backend/.venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r backend/requirements.txt
	$(VENV_PIP) freeze > backend/requirements.lock.txt
	npm --prefix frontend ci

db-up:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)
	set -a; . ./$(ENV_FILE); set +a; docker compose up -d postgres

db-down:
	docker compose down

migrate:
	set -a; . ./$(ENV_FILE); set +a; cd backend && ../$(VENV_PYTHON) -m alembic -c alembic.ini upgrade head

backend:
	set -a; . ./$(ENV_FILE); set +a; $(VENV_PYTHON) -m uvicorn app.main:app --app-dir backend --host "$${API_HOST:-127.0.0.1}" --port "$${API_PORT:-8000}"

frontend:
	set -a; . ./$(ENV_FILE); set +a; npm --prefix frontend run dev

test:
	$(VENV_PYTHON) -m pytest backend/tests
	npm --prefix frontend test

test-integration:
	set -a; . ./$(ENV_FILE); set +a; $(VENV_PYTHON) -m pytest backend/tests -m integration

lint:
	$(VENV_PYTHON) -m ruff check backend
	npm --prefix frontend run lint

typecheck:
	$(VENV_PYTHON) -m mypy backend/app
	npm --prefix frontend run typecheck

build:
	npm --prefix frontend run build

stop:
	-docker compose stop postgres
	-pkill -f "uvicorn app.main:app" || true
	-pkill -f "next dev" || true

reset:
	@echo "!!! WARNING: this destroys the local PostgreSQL volume and all local data !!!"
	@test "$${CONFIRM:-}" = "yes" || (echo "Refusing reset: rerun with CONFIRM=yes"; exit 1)
	docker compose down -v

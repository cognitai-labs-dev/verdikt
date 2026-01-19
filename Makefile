.PHONY: help
help: # Show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m: $$(echo $$l | cut -f 2- -d'#')\n"; done

TA ?= -v tests/

upgrade-db:
	uv run alembic upgrade head

ruff-lint: # Run ruff linter
	uv run ruff check --fix src/

ruff-format: # Run ruff formatter
	uv run ruff format src/

mypy: # Run mypy type checker
	uv run mypy src/

lint: # Run pre-commit
	pre-commit run --all-files

venv: # Create venv
	uv venv --allow-existing .venv

up-d: # Run database in the background
	docker compose up -d

down:
	docker compose down 

cli: # Run cli application
	uv run main.py cli

web: up-d # Run web application
	uv run main.py web

slack: up-d # Run slack application
	uv run main.py slack

db: # enter db prompt
	psql postgresql://postgresql:alpharius@localhost:5432

pdb: # enter db prompt
	pgcli postgresql://postgresql:alpharius@localhost:5432

test: # Run tests
	uv run pytest $(TA)

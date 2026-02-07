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

api: up-d upgrade-db # Run api
	uv run main.py api

create-app: # Create the ai-oncall-assistant app
	uv run main.py create-app

create-datasets: # Create datasets for app (usage: make create-datasets APP_ID=1)
	uv run main.py create-datasets $(APP_ID)

eval: # Create evaluation (usage: make eval APP_ID=1 TYPE=HUMAN_AND_LLM)
	uv run main.py evaluate $(APP_ID) $(TYPE)

judge: # Judge evals
	uv run main.py run-judging

up-d: # Run database in the background
	docker compose up -d

down:
	docker compose down

db: # enter db prompt
	psql postgresql://postgresql:alpharius@localhost:5432

test: # Run tests
	uv run pytest $(TA)

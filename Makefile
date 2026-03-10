.PHONY: help
help: # Show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m: $$(echo $$l | cut -f 2- -d'#')\n"; done

TA ?= -v tests/

upgrade-db:
	cd backend && uv run alembic upgrade head

ruff-lint: # Run ruff linter
	cd backend && uv run ruff check --fix src/

ruff-format: # Run ruff formatter
	cd backend && uv run ruff format src/

mypy: # Run mypy type checker
	cd backend && uv run mypy src/

lint: # Run pre-commit
	pre-commit run --all-files

api: up-d upgrade-db # Run api
	cd backend && uv run main.py api

eval: # Run eval
	cd backend && uv run main.py evaluate HUMAN_AND_LLM
	cd backend && uv run main.py evaluate LLM_ONLY

judge: # Judge evals
	cd backend && uv run main.py run-judging

up-d: # Run database in the background
	docker compose up -d

down:
	docker compose down

db: # enter db prompt
	psql postgresql://postgresql:alpharius@localhost:5432

test: # Run tests
	cd backend && uv run pytest $(TA)

fe:
	cd frontend && pnpm run dev

api-gen:
	cd frontend && pnpm run api:generate

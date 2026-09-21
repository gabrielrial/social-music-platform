# Rate API - shortcuts for the most common commands.
# Run `make` (or `make help`) to see what is available.

COMPOSE = docker compose -f docker/docker-compose.yml
VENV    = .venv/bin

# These targets are command names, not files. Without this, `make test`
# would do nothing because a folder called `test/` already exists.
.PHONY: help install db-up run seed seed-reset test down db-drop clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  make %-10s %s\n", $$1, $$2}'

install: ## Create .venv and install the dependencies
	python3 -m venv .venv
	$(VENV)/pip install -r requirements.txt

db-up: ## Start the development database (port 5432)
	$(COMPOSE) up -d --wait db

run: db-up ## Start the dev database and the API with auto-reload
	$(VENV)/uvicorn app.main:app --reload

seed: db-up ## Fill the dev database with sample users, posts, genres and likes
	$(VENV)/python -m scripts.seed_dev

seed-reset: db-up ## Wipe the dev database tables and seed them again (asks first)
	@printf "This deletes ALL development data and loads the sample data. Continue? [y/N] "; \
	read answer; \
	if [ "$$answer" = "y" ]; then \
		$(VENV)/python -m scripts.seed_dev --reset; \
	else \
		echo "Cancelled."; \
	fi

test: ## Start the test database (port 5433) and run the tests
	$(COMPOSE) up -d --wait db_test
	$(VENV)/pytest -v

down: ## Stop the containers (development data is kept)
	$(COMPOSE) down

db-drop: ## Stop the containers and DELETE the development database (asks first)
	@printf "This deletes ALL development data (users, posts, comments). Continue? [y/N] "; \
	read answer; \
	if [ "$$answer" = "y" ]; then \
		$(COMPOSE) down -v && echo "Database deleted. 'make run' will create an empty one."; \
	else \
		echo "Cancelled."; \
	fi

clean: ## Remove Python and pytest caches
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .pytest_cache

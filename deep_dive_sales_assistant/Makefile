.PHONY: test install clean format lint help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	poetry install

test:  ## Run tests
	poetry run pytest -v

format:  ## Format code
	poetry run black .
	poetry run isort .

lint:  ## Run linting
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy src/

clean:  ## Clean cache files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

run-example:  ## Run example (requires API keys)
	poetry run deepdive "Shopify" --verbose 
.PHONY: run test lint

run:
	docker-compose up --build

test:
	poetry run pytest -v

lint:
	poetry run ruff check src
	poetry run mypy src

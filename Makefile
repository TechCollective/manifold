.PHONY: all install run-cli run-web test lint format dev clean lint-plugins

install:
	poetry install

run-cli:
	poetry run manifold $(ARGS)

run-web:
	FLASK_APP=manifold_web.app FLASK_ENV=development poetry run flask run

test:
	poetry run pytest -v

lint:
	poetry run black . --check
	poetry run isort . --check
	poetry run mypy manifold_core/ manifold_cli/ manifold_web/

format:
	poetry run black .
	poetry run isort .

dev:
	make run-web

clean:
	find . -name "*.pyc"*

lint-plugins:
	poetry run python scripts/lint_plugins.py

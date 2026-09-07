VENV := .venv
PROJECT_NAME :=  $(notdir $(CURDIR))
FOLDER := src
LINT := flake8 . && mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
LINT-STRICT := flake8 . && mypy . --strict

.PHONY: help install run debug clean fclean erase lint lint-strict push

help:
	@echo "install:		Install project and its dependancies."; \
	echo "run:			Launch project."; \
	echo "debug:			Launch debug mode."; \
	echo "clean:			Remove all cache files."; \
	echo "fclean:			Remove Virtual Env and cache files."; \
	echo "erase:			Remove pyproject.toml, Virtual Env and cache files."; \
	echo "lint:			Testing Flake8 and Mypy."; \
	echo "lint-strict:		Testing flake8 and Mypy in strict mode."; \
	echo "push:			Push project (Only for devs).";

install:
	@if [ ! -f "pyproject.toml" ]; then \
		uv init --bare --name "$(PROJECT_NAME)" ; \
		printf "\033[0;33m[INFO]\033[0m Downloading dependencies for project...\n"; \
		uv add pydantic; \
		printf "\033[0;33m[INFO]\033[0m  Downloading dev dependancies for project..."; \
		uv add --dev mypy flake8 flake8-docstrings; \
	fi; \
	uv sync

run: install
	@uv run python -m $(FOLDER)

debug:

clean:
	@find . -type d \( -name .mypy_cache -o -name __pycache__ \) -prune -exec rm -rf {} \;

fclean: clean
	@rm -rf ${VENV}

erase: fclean
	@rm -f pyproject.toml uv.lock

lint:
	@cd $(FOLDER) && ${LINT}

lint-strict:
	@cd $(FOLDER) && ${LINT-STRICT}

push:
	@set -e; \
	read -p "Commit message: " MESSAGE; \
	git add .; \
	git commit -m "$$MESSAGE"; \
	git push
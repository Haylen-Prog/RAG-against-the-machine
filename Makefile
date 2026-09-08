VENV := .venv
PROJECT_NAME := $(notdir $(CURDIR))
FOLDER := src
ARCHIVE := data+moulinette.tar.xz

MYPY_FLAGS := \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs
LINT-STRICT := flake8 . && mypy . --strict

.PHONY: help install run debug clean fclean erase lint lint-strict push

help:
	@echo "install:		Install project and its dependencies."; \
	echo "run:			Launch project."; \
	echo "debug:			Launch debug mode."; \
	echo "clean:			Remove all cache files."; \
	echo "fclean:			Remove Virtual Env and cache files."; \
	echo "erase:			Remove pyproject.toml, Virtual Env and cache files."; \
	echo "lint:			Testing Flake8 and Mypy."; \
	echo "lint-strict:		Testing flake8 and Mypy in strict mode."; \
	echo "push:			Push project (Only for devs).";

install:
	@mkdir -p /goinfre/$${USER}/containers/$(PROJECT_NAME)

	@if [ -f "${ARCHIVE}" ]; then \
		tar -xf ${ARCHIVE}; \
		unzip moulinette.zip -d moulinette; \
		unzip vllm-0.10.1.zip -d vllm-0.10.1; \
		unzip datasets_public.zip -d datasets_public; \
		rm -rf *.zip *.tar.xz ;\
		mkdir -p data/raw && mv vllm-0.10.1 datasets_public data/raw; \
	else \
		echo "Caution there is no '${ARCHIVE}', in folder '${PROJECT_NAME}' continue ? [n/Y]"; \
		echo ""; \
		ANSWER=""; \
		while [ "$$ANSWER" != 'Y' ] && [ "$$ANSWER" != 'n' ]; do \
			read -p ">>> " ANSWER; \
		done; \
		if [ "$$ANSWER" = 'n' ]; then \
			echo "Installation was aborted."; \
			exit 0; \
		fi; \
	fi

	@if [ ! -f "pyproject.toml" ]; then \
		uv init --bare --name "$(PROJECT_NAME)"; \
		( cd /goinfre/$${USER}/containers/$(PROJECT_NAME) && uv venv ); \
		rm -rf .venv; \
		ln -s /goinfre/$${USER}/containers/$(PROJECT_NAME)/.venv .venv; \
		printf "\033[0;33m[INFO]\033[0m Downloading dependencies for project...\n"; \
		uv add pydantic; \
		printf "\033[0;33m[INFO]\033[0m  Downloading dev dependencies for project..."; \
		uv add --dev mypy flake8 flake8-docstrings; \
	fi

run: install
	@uv run python -m $(FOLDER)


debug:

clean:
	@find . -type d \( -name .mypy_cache -o -name __pycache__ \) -prune -exec rm -rf {} \;

fclean: clean
	@rm -rf ${VENV} /goinfre/$${USER}/containers/$(PROJECT_NAME)


erase: fclean
	@rm -rf pyproject.toml uv.lock data moulinette

lint:
	@cd $(FOLDER) && flake8 . && mypy . $(MYPY_FLAGS)

lint-strict:
	@cd $(FOLDER) && flake8 . && mypy . --strict

push:
	@set -e; \
	read -p "Commit message: " MESSAGE; \
	git add .; \
	git commit -m "$$MESSAGE"; \
	git push
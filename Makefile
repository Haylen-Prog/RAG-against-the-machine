VENV := .venv
PROJECT_NAME := $(notdir $(CURDIR))
FOLDER := src
ARCHIVE := data+moulinette.tar.xz
PROJECT_DIR := /goinfre/$${USER}/containers/$(PROJECT_NAME)

MYPY_FLAGS := \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

.PHONY: help install run debug clean fclean erase lint lint-strict push

help:
	@printf '%s\n' \
			"install:		Install project and its dependencies." \
			"run:			Launch project." \
			"debug:			Launch debug mode." \
			"clean:			Remove all cache files." \
			"fclean:			Remove Virtual Env and cache files." \
			"erase:			Remove pyproject.toml, Virtual Env and cache files." \
			"lint:			Testing Flake8 and Mypy." \
			"lint-strict:		Testing flake8 and Mypy in strict mode." \
			"push:			Push project (Only for devs)."


install:
	@if [ ! -d "data" ]; then \
		mkdir -p "$(PROJECT_DIR)"; \
		if [ -f "$(ARCHIVE)" ]; then \
			( \
				cp "$(ARCHIVE)" "$(PROJECT_DIR)" && \
				cd "$(PROJECT_DIR)" && \
				tar -xf "$(notdir $(ARCHIVE))" && \
				unzip moulinette.zip -d moulinette && \
				unzip vllm-0.10.1.zip -d vllm-0.10.1 && \
				unzip datasets_public.zip -d datasets_public && \
				rm -f moulinette.zip vllm-0.10.1.zip datasets_public.zip && \
				rm -f "$(notdir $(ARCHIVE))" && \
				mkdir -p data/raw && \
				mv vllm-0.10.1 datasets_public data/raw \
			); \
			ln -s "$(PROJECT_DIR)/data" data; \
		else \
			echo "Caution there is no "$(ARCHIVE)", in folder "$(PROJECT_NAME)" continue ? [n/Y]"; \
			echo ""; \
			ANSWER=""; \
			while [ "$$ANSWER" != 'Y' ] && [ "$$ANSWER" != 'n' ]; do \
				printf ">>> "; \
				read ANSWER; \
			done; \
			if [ "$$ANSWER" = 'n' ]; then \
				echo "Installation was aborted."; \
				exit 1; \
			fi; \
		fi; \
	else \
		printf "Already installed \n"; \
	fi

	@if [ ! -f "pyproject.toml" ]; then \
		uv init --bare --name "$(PROJECT_NAME)"; \
		( cd "$(PROJECT_DIR)" && uv venv ); \
		rm -rf .venv; \
		ln -s "$(PROJECT_DIR)"/.venv .venv; \
		printf "\033[0;33m[INFO]\033[0m Downloading dependencies for project...\n"; \
		uv add pydantic; \
		printf "\033[0;33m[INFO]\033[0m  Downloading dev dependencies for project..."; \
		uv add --dev mypy flake8 flake8-docstrings; \
	fi

run: install
	@uv run python -m "$(FOLDER)" --max_chunk_size 1500


debug:

clean:
	@find . -type d \( -name ".mypy_cache" -o -name "__pycache__" \) -prune -exec rm -rf {} \;

fclean: clean
	@rm -rf "$(VENV)" "$(PROJECT_DIR)"


erase: fclean
	@rm -rf pyproject.toml uv.lock data moulinette

lint:
	@cd "$(FOLDER)" && flake8 . && mypy . "$(MYPY_FLAGS)"

lint-strict:
	@cd "$(FOLDER)" && flake8 . && mypy . --strict

push:
	@set -e; \
	printf "Commit message: "; \
	read MESSAGE; \
	git add . && \
	git commit -m "$$MESSAGE" && \
	git push
# Makefile

FOLDER := src
PROJECT_NAME := $(notdir $(CURDIR))
ARCHIVE := data+moulinette.tar.xz
PROJECT_DIR := /goinfre/${USER}/containers/$(PROJECT_NAME)

ifneq ($(wildcard /goinfre/$(USER)),)
export UV_PROJECT_ENVIRONMENT := $(PROJECT_DIR)/.venv
export UV_CACHE_DIR           := /goinfre/$(USER)/.cache/uv
export HF_HOME                := /goinfre/$(USER)/.cache/huggingface
endif

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
			 --ignore-missing-imports --disallow-untyped-defs \
			 --check-untyped-defs 


.PHONY: help install run debug clean fclean erase re lint lint-strict \
        setup-data add mouli search-all search-smoke answer-smoke \
        edge-cases review-tests push

help:
	@printf '%s\n' \
		"install:     Install dependencies (uv sync)." \
		"run:         Index the corpus (default chunk size 2000)." \
		"search-all:  Search both public datasets." \
		"search-smoke: Run the documented single-query search example." \
		"answer-smoke: Run the documented single-query answer example." \
		"mouli:       Search and evaluate both public datasets." \
		"edge-cases:  Run the four robustness checks from Reivew.md." \
		"review-tests: Run indexing, retrieval evaluation, answer and edge checks." \
		"debug:       Run the same command under pdb." \
		"clean:       Remove cache files." \
		"fclean:      clean + remove .venv." \
		"fclean-data: Remove the goinfre copy (data, moulinette, venv)." \
		"re:          fclean + run." \
		"lint:        flake8 + mypy." \
		"lint-strict: flake8 + mypy --strict." \
		"setup-data:  Unpack data+moulinette into goinfre (dev machine only)." \
		"push:        Commit and push (devs only)."

# Mandatory rules

install:
	@uv sync

run: install
	@uv run ollama serve > ollama.log 2>&1 &
	@until curl -fsS http://localhost:11434/api/tags >/dev/null; do sleep 1; done
	@ollama pull qwen3:0.6b
	@uv run python -m "$(FOLDER)" index --max_chunk_size 2000

debug: install
	@uv run python -m pdb -m $(FOLDER) index --max_chunk_size 2000

clean:
	@find . -type d \( -name ".mypy_cache" -o -name "__pycache__" \) -prune -exec rm -rf {} \;

fclean: clean
	@rm -rf .venv
	@rm -f data/processed/chunk.jsonl

lint: install
	@uv run flake8 $(FOLDER)
	@uv run mypy $(FOLDER) $(MYPY_FLAGS)

lint-strict: install
	@uv run flake8 $(FOLDER)
	@uv run mypy $(FOLDER) --strict

# Extras


test:
	uv run mypy src/ --strict --follow-untyped-imports

setup-data:
	@if [ -d "$(PROJECT_DIR)/data" ]; then \
		echo "Data already unpacked in $(PROJECT_DIR)"; \
	elif [ ! -f "$(ARCHIVE)" ]; then \
		echo "Error: '$(ARCHIVE)' not found in $(CURDIR)"; \
		exit 1; \
	else \
		mkdir -p "$(PROJECT_DIR)" && \
		cp "$(ARCHIVE)" "$(PROJECT_DIR)" && \
		cd "$(PROJECT_DIR)" && \
		tar -xf "$(notdir $(ARCHIVE))" && \
		unzip -q moulinette.zip -d moulinette && \
				unzip -q vllm-0.10.1.zip && \
		unzip -q datasets_public.zip -d datasets_public && \
		rm -f moulinette.zip vllm-0.10.1.zip datasets_public.zip \
		      "$(notdir $(ARCHIVE))" && \
		mkdir -p data/raw && \
		mv vllm-0.10.1 data/raw/ && \
		mv datasets_public data/datasets; \
	fi
	@ln -sfn "$(PROJECT_DIR)/data" data
	@ln -sfn "$(PROJECT_DIR)/moulinette" moulinette

add: 
	@uv add $(PKG)

remove:
	@uv remove $(PKG)

RES := $(CURDIR)/data/output/search_results/UnansweredQuestions
GT  := $(CURDIR)/data/datasets/public/AnsweredQuestions

search-all: install
	@for d in docs code; do \
		uv run python -m src search_dataset \
			--dataset_path data/datasets/public/UnansweredQuestions/dataset_$${d}_public.json \
			--k 10 \
			--save_directory data/output/search_results/UnansweredQuestions; \
	done

search-smoke: install
	@uv run python -m src search "How to configure OpenAI server?" --k 10

answer-smoke: install
	@uv run python -m src answer "How to configure OpenAI server?" --k 10

edge-cases: install
	@set -eu; \
	log=$$(mktemp); \
	trap 'rm -f "$$log"' EXIT; \
	run_case() { \
		label=$$1; shift; \
		if ! uv run "$$@" >"$$log" 2>&1; then \
			echo "FAIL: $$label (command failed)"; \
			cat "$$log"; \
			exit 1; \
		fi; \
		if grep -q "Traceback (most recent call last)" "$$log"; then \
			echo "FAIL: $$label (traceback found)"; \
			cat "$$log"; \
			exit 1; \
		fi; \
		echo "PASS: $$label (no traceback)"; \
	}; \
	run_case "empty search query" python -m src search "" --k 10; \
	run_case "nonsense search query" python -m src search asdfghjkl --k 10; \
	run_case "answer with k=0" python -m src answer "What is vLLM?" --k 0; \
	run_case "missing dataset path" python -m src search_dataset \
		--dataset_path /nonexistent.json \
		--save_directory data/output/edge-cases --k 10

review-tests: run mouli search-smoke answer-smoke edge-cases

mouli: search-all
	@cd moulinette/moulinette_pkg && \
	for d in docs code; do \
		echo "== $$d"; \
		./moulinette-fedora evaluate_student_search_results \
			$(RES)/dataset_$${d}_public.json \
			$(GT)/dataset_$${d}_public.json \
			--k 10 --max_context_length 2000; \
	done

erase: fclean
	@rm -rf "$(PROJECT_DIR)"
	@rm -rf data moulinette; \

re: fclean run

push:
	@set -e; \
	printf "Commit message: "; \
	read MESSAGE; \
	git add . && git commit -m "$$MESSAGE" && git push
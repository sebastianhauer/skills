# Developer entry points for the skills repo. `make check` is the gate
# that the pre-push hooks and CI both run, so local == CI.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

UV ?= uv

.PHONY: help bootstrap format check check-python check-types \
	check-markdown check-unit validate release-check

help: ## Display this help
	@awk '\
		BEGIN \
		{ \
			FS = ":.*##"; \
			print "\nUsage:\n  make \033[36m<target>\033[0m\n" \
		} \
		/^[a-zA-Z_0-9-]+:.*?##/ \
		{ \
			printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 \
		} \
		/^##@/ \
		{ \
			printf "\n\033[1m%s\033[0m\n", substr($$0, 5) \
		}' $(MAKEFILE_LIST)

##@ Setup

bootstrap: ## Rebuild the vanilla stock 3.9 venv and install git hooks
	rm -rf .venv
	$(UV) python install 3.9
	$(UV) venv --python 3.9
	$(UV) sync
	$(UV) run pre-commit install --hook-type pre-commit \
		--hook-type commit-msg --hook-type pre-push

format: ## Auto-fix: ruff (lint --fix + format) then mdformat
	$(UV) run ruff check --fix .
	$(UV) run ruff format .
	git ls-files -z '*.md' | xargs -0 $(UV) run mdformat --wrap 80

##@ Quality gates

check: check-python check-types check-markdown check-unit ## Run all gates
	@echo "make check: all gates passed"

check-python: ## py_compile (3.9 syntax floor) + ruff lint + format check
	git ls-files -z '*.py' | xargs -0 $(UV) run python -m py_compile
	$(UV) run ruff check .
	$(UV) run ruff format --check .

check-types: ## pyright + mypy (both target 3.9)
	$(UV) run pyright
	$(UV) run mypy

check-markdown: ## mdformat --check + markdownlint over all Markdown
	git ls-files -z '*.md' | xargs -0 $(UV) run mdformat --wrap 80 --check
	$(UV) run pre-commit run markdownlint-cli2 --all-files

check-unit: ## pytest: example unit + CLI + import-smoke net
	$(UV) run pytest

validate: ## Validate the plugin/marketplace manifest (needs claude CLI)
	claude plugin validate . --strict

##@ Release

release-check: check validate ## Full gate before publishing or pushing
	@echo "release-check: all release gates passed"

PYTHON ?= python3.11
VENV_NAME ?= venv
RUN = $(VENV_NAME)/bin/python

venv:
	$(PYTHON) -m venv $(VENV_NAME)
	$(RUN) -m pip install -e . pytest pytest-asyncio ruff build

lint:
	$(RUN) -m ruff check extend tests tools

test:
	$(RUN) -m pytest -q

build:
	$(RUN) -m build

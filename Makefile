PYTHON ?= python3.11
VENV_NAME ?= venv
RUN = $(VENV_NAME)/bin/python

venv:
	$(PYTHON) -m venv $(VENV_NAME)
	$(RUN) -m pip install -e . pytest pytest-asyncio ruff build

lint:
	$(RUN) -m ruff check extend tests/test_transport_security.py tools

test:
	$(RUN) -m pytest -q tests/test_transport_security.py

build:
	$(RUN) -m build

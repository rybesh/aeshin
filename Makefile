PYTHON := ./venv/bin/python
PIP := ./venv/bin/python -m pip
.DEFAULT_GOAL := run

$(PYTHON):
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: | $(PYTHON)
	$(PYTHON) -Werror manage.py runserver

migrations: | $(PYTHON)
	$(PYTHON) manage.py makemigrations

migrate: | $(PYTHON)
	$(PYTHON) manage.py migrate

clean:
	rm -rf venv

.PHONY: run migrations migrate clean

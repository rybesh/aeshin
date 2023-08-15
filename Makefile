PYTHON := ./venv/bin/python
PIP := ./venv/bin/python -m pip
APP := aeshin
HOST := aeshin.org
REGION := iad
READINGS := media/courses/readings
.DEFAULT_GOAL := run

$(PYTHON):
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

migrations: | $(PYTHON)
	$(PYTHON) manage.py makemigrations

migrate: | $(PYTHON)
	$(PYTHON) manage.py migrate

collectstatic: | $(PYTHON)
	$(PYTHON) manage.py collectstatic --noinput

run: migrate collectstatic | $(PYTHON)
	$(PYTHON) -Werror manage.py runserver

launch:
	fly launch \
	--auto-confirm \
	--copy-config \
	--ignorefile .dockerignore \
	--dockerfile Dockerfile \
	--region $(REGION) \
	--name $(APP)
	@echo "Next: make volume"

volume:
	fly volumes create data --region $(REGION)
	fly volumes list
	@echo "Next: make secrets"

secrets:
	cat .env.prod | fly secrets import
	@echo
	fly secrets list
	@echo "Next: make deploy"

deploy:
	fly deploy
	@echo "Next: make wireguard"

wireguard:
	fly wireguard create
	fly wireguard list
	@echo "Next: make rsync"

rsync:
	rsync -avz db.sqlite root@$(APP).internal:/mnt/data/db.sqlite
	ssh root@$(APP).internal mkdir -p /mnt/data/$(READINGS)
	rsync -avz $(READINGS)/ root@$(APP).internal:/mnt/data/$(READINGS)/
	@echo "Next: make ips"

ips:
	@echo "Add A and AAAA records for $(HOST)":
	fly ips list
	@echo "Next: make certs"

certs:
	fly certs create $(HOST)
	fly certs show $(HOST)

clean:
	rm -rf venv static

.PHONY: migrations migrate collectstatic run launch volume secrets deploy wireguard rsync certs destroy clean

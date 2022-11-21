dc_config/secrets.env:
# Creating secrets file for editing
ifndef EDITOR
ifeq ($(strip $(shell which nano)),)
$(error dc_config/secrets.env will need to be manually created. Copy dc_config/secrets_template.env as a starting point)
endif
endif
	@cp dc_config/secrets_template.env dc_config/secrets.env
	@$${EDITOR:-nano} dc_config/secrets.env


include dc_config/cybercom_config.env
include dc_config/secrets.env

# Set GITPOD_PORT to 8080 if run in gitpod
ifneq ($(strip $(GITPOD_WORKSPACE_ID)),)
	GITPOD_PORT = 8080
	ALLOWED_HOSTS = .gitpod.io,localhost
endif

ifeq ($(strip $(shell docker compose 1>/dev/null && echo 0)),0)
	COMPOSE := docker compose
else
	COMPOSE := docker-compose
endif

COMPOSE_INIT = $(COMPOSE) -f dc_config/images/docker-compose-init.yml
CERTBOT_INIT = $(COMPOSE) -f dc_config/images/certbot-initialization.yml
DJANGO_MANAGE = $(COMPOSE) run --rm cybercom_api ./manage.py

SHELL = /bin/bash

.PHONY: init intidb initssl cert_dates superuser migrate flush init_certbot renew_certbot \
	shell apishell celeryshell dbshell build force_build run stop test restart_api collectstatic

.EXPORT_ALL_VARIABLES:
UID=$(shell id -u)
GID=$(shell id -g)

init: 
	$(COMPOSE_INIT) build
	$(COMPOSE_INIT) up
	$(COMPOSE_INIT) down

initdb:
	$(COMPOSE_INIT) up cybercom_mongo_init
	$(COMPOSE_INIT) down

initssl:
	$(COMPOSE_INIT) build cybercom_openssl_init
	$(COMPOSE_INIT) up cybercom_openssl_init
	$(COMPOSE_INIT) down

cert_dates:
	# Show valid date ranges for backend ssl certificates
	@$(COMPOSE_INIT) run --rm cybercom_openssl_init openssl x509 -noout -dates -in /ssl/server/cert.pem

superuser:
	@$(DJANGO_MANAGE) createsuperuser 

migrate:
	@$(DJANGO_MANAGE) migrate

flush:
	@$(DJANGO_MANAGE) flush

init_certbot:
	$(CERTBOT_INIT) build
	$(CERTBOT_INIT) up --abort-on-container-exit
	$(CERTBOT_INIT) down

renew_certbot:
	$(CERTBOT_INIT) run --rm cybercom_certbot
	# This requires an init process running in the container
	# https://docs.docker.com/compose/compose-file/compose-file-v3/#init
	@$(COMPOSE) exec cybercom_nginx nginx -s reload

shell:
	@echo "Loading new shell with configured environment"
	@$(SHELL)

apishell:
	@echo "Launching shell into Django"
	@$(COMPOSE) exec cybercom_api python manage.py shell

celeryshell:
	@echo "Lanuching shell into Celery"
	@$(COMPOSE) exec cybercom_celery celery shell

dbshell:
	@echo "Launching shell into MongoDB"
	@$(COMPOSE) exec cybercom_mongo mongosh  \
		--tls \
		--host cybercom_mongo \
		--tlsCertificateKeyFile /ssl/client/mongodb.pem \
		--tlsCAFile /ssl/testca/cacert.pem \
		--username $$MONGO_USERNAME \
		--password $$MONGO_PASSWORD

build:
	@$(COMPOSE) --compatibility build

force_build:
	@$(COMPOSE) --compatibility build --no-cache

run:
	@$(COMPOSE) --compatibility up -d

stop:
	@$(COMPOSE) --compatibility down

test:
	@$(COMPOSE) exec cybercom_api python -Wa manage.py test

restart_api:
	@$(COMPOSE) restart cybercom_api

collectstatic: 
	@mkdir -p web/static
	@$(COMPOSE) run --rm cybercom_api ./manage.py collectstatic --noinput

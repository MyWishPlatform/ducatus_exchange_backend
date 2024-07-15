.PHONY: test 
lines := 1000
compose := docker compose

init: init-envs pre-commit

init-envs:
	cp env.example .env
	cp config.example.yaml config.yaml
	mkdir logs

test:
	sudo $(compose) -f test.yml up --build --abort-on-container-exit

build:
	sudo $(compose) up --build -d 

down:
	sudo $(compose) down

stop:
	sudo $(compose) stop

ps:
	sudo $(compose) ps

full-migrate: makemigrations migrate

makemigrations:
	sudo $(compose) exec web python ./manage.py makemigrations
migrate:
	sudo $(compose) exec web python ./manage.py migrate

shell:
	sudo $(compose) exec web python ./manage.py shell_plus

collectstatic:
	sudo $(compose) exec web python ./manage.py collectstatic

admin:
	sudo $(compose) exec web python ./manage.py createsuperuser

web-build:
	sudo $(compose) up --build -d web

web-logs:
	sudo $(compose) logs --tail $(lines) -f web

all-logs:
	sudo $(compose) logs --tail $(lines) -f

celery-build:
	sudo $(compose) up --build -d celery celery_beat

celery-logs:
	sudo $(compose) logs --tail $(lines) -f celery celery_beat

celery-stop:
	sudo $(compose) stop celery celery_beat


scanner-logs:
	sudo $(compose) logs --tail $(lines) -f scanner

scanner-stop:
	sudo $(compose) stop scanner

scanner-build:
	sudo $(compose) up --build -d scanner

redis-cli:
	sudo $(compose) exec redis redis-cli

pg-shell:
	sudo $(compose) exec db bash

fixtures: web-build
	sudo $(compose) exec web python manage.py create_fixtures_networks



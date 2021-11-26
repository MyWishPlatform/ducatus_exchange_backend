shell:
	sudo docker-compose exec web python manage.py shell_plus

build_and_run:
	sudo docker-compose build --parallel && sudo docker-compose up -d
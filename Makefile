shell:
	sudo docker-compose exec web python manage.py shell_plus

run:
	sudo docker-compose build --parallel && sudo docker-compose up -d
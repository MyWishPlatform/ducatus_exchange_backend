#!/bin/sh

echo "Flush the manage.py command it any"

while ! python manage.py makemigrations 2>&1; do
  echo "Makemigrations is in progress status"
  sleep 3
done

while ! python manage.py flush --no-input 2>&1; do
  echo "Flushing django manage command"
  sleep 3
done

# Wait for few minute and run db migration
while ! python manage.py migrate 2>&1; do
  echo "Migrate is in progress status"
  sleep 3
done

echo "Django docker is fully configured successfully."

exec "$@"
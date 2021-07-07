#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres not run yet..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "Postgres RUN"
fi

exec "$@"
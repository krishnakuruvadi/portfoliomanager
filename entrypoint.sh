#!/bin/sh

if [ "DB_ENGINE" = "postgresql" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done

    echo "PostgreSQL started"
fi

sleep 5

python manage.py makemigrations
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py createsuperuser --no-input

# Both processes need to run simultaneously and will remain open until the container is stopped.
gunicorn portfoliomgr.wsgi:application --user www-data --bind 0.0.0.0:8020 --workers 3 & PIDGUNICORN=$!
python manage.py run_huey & PIDHUEY=$!

wait $PIDGUNICORN
wait $PIDHUEY

exec "$@"

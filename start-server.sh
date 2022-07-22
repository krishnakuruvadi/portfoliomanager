#!/usr/bin/env bash
# start-server.sh
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd portfoliomanager; python manage.py createsuperuser --no-input;cd ..)
fi
echo `pwd`
ls
(cd portfoliomanager;ls; python manage.py migrate;gunicorn portfoliomgr.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3) &
nginx -g "daemon off;"
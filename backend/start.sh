#!/bin/sh
set -e
python manage.py migrate
python manage.py seed --reset
exec gunicorn config.wsgi --bind "0.0.0.0:${PORT:-8000}" --workers 2 --log-file -

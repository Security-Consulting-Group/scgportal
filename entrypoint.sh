
#!/bin/sh

echo '======> Running collectstatic...'
python manage.py collectstatic --no-input --settings=config.settings.production

echo '\n======> Applying migrations...'
python manage.py makemigrations --settings=config.settings.production
python manage.py migrate --settings=config.settings.production

echo '\n======> Running server...'
gunicorn --env DJANGO_SETTINGS_MODULE=config.settings.production config.wsgi:application --bind 0.0.0.0:8000 --workers 1

# uwsgi --http :8000 --module config.wsgi:application --env DJANGO_SETTINGS_MODULE=config.settings.production --master --workers 4 --enable-threads --socket /tmp/uwsgi.sock --chmod-socket=664 --vacuum --die-on-term --thunder-lock
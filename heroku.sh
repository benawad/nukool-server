celery worker -A app.celery --loglevel=info &
gunicorn -w 4 -b 0.0.0.0:$PORT -k gevent app:app

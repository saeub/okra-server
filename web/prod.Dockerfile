FROM python:3.12

ENV DJANGO_SETTINGS_MODULE=okra_server.settings_prod

COPY . /app
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.prod.txt

RUN python manage.py collectstatic --noinput

CMD gunicorn okra_server.wsgi --bind 0.0.0.0:8000

FROM python:3.10

RUN mkdir /app
COPY requirements.common.txt requirements.dev.txt /app/
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.dev.txt

CMD python manage.py runserver 0.0.0.0:8000

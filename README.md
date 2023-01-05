# okra-server

This is an implementation of a server and API for [Okra](https://github.com/saeub/okra), including a dashboard for configuring and monitoring experiments. It is implemented as a Django web app which can be used and adapted to configure and serve experiments to participants.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with [Docker Compose](https://docs.docker.com/compose/install/)

If you prefer not to use Docker for development or production, the Django app can also be run directly. In this case, use Python >= 3.6 and install `web/requirements.dev.txt` or `web/requirements.prod.txt`.

## Development setup

With this setup, the Django app is run inside a Docker container

- Build container images:
  ```bash
  $ docker compose -f docker-compose.prod.yaml build
  ```
- Initialize database and superuser:
  ```bash
  $ docker compose -f docker-compose.dev.yaml run web-dev python manage.py migrate
  $ docker compose -f docker-compose.dev.yaml run web-dev python manage.py createsuperuser
  ```
- Start it up!
  ```bash
  $ docker compose -f docker-compose.dev.yaml up
  ```
- Access your API at [localhost:8000](http://localhost:8000)
- Run tests:
  ```bash
  $ docker compose -f docker-compose.dev.yaml run web-dev pytest
  ```

If you are using Visual Studio Code, you can use the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) to develop inside the running container.

## Production setup

- Create `.env` file (see `.env.example` for an example)
- Build container images:
  ```bash
  $ docker compose -f docker-compose.prod.yaml build
  ```
- Start it up!
  ```bash
  $ docker compose -f docker-compose.prod.yaml up -d
  ```
- Initialize database and superuser:
  ```bash
  $ docker compose -f docker-compose.prod.yaml exec postgres createdb -U my_db_user okra_server
  $ docker compose -f docker-compose.prod.yaml exec web python manage.py migrate
  $ docker compose -f docker-compose.prod.yaml exec web python manage.py createsuperuser
  ```
- Collect static files:
  ```bash
  $ docker compose -f docker-compose.prod.yaml exec web python manage.py collectstatic
  ```

Your API will be accessible through the port you specified in your `.env`. If you change anything in your `.env`, run `docker compose -f docker-compose.prod.yaml up -d` again. To shut down the server, run `docker compose -f docker-compose.prod.yaml down`.

# Theatre API

API service for theatre management written on DRF

## Installing using GitHub

Install PostgreSQL and create db

```python
git clone https://github.com/hbilous/theatre-service.git
cd theatre_service
python -m venv venv
venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
## Run with docker

```python
docker-compose build
docker-compose up
```

## Getting access

* Create user via api/user/register
* Get access token via api/user/token

## Features

* JWT Authenticated
* Admin panel /admin/
* Documentation is located at /api/doc/swagger/
* Managing orders and tickets
* Create plays with genres and actors
* Creating theatre halls
* Adding performances
* Filtering plays and performances
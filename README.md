# Nordic Microalgae: Backend

![CI/CD status](https://github.com/nordicmicroalgae/backend/actions/workflows/main.yml/badge.svg)

This repository contains source code for the backend used in Nordic Microalgae.

The backend consists of a REST API and administration interface and is written in Python and uses, as of writing, the latest <attr title="Long Term Support">LTS</attr> version (4.2) of Django as web framework.
PostgreSQL is used as datbase layer and JSONB is being used heavily to store generated information in read-only tables, as well as for storing metadata in some of the user-writable tables.

## Install and run locally

Clone backend and content repos:

```
mkdir -p ~/code/nordicmicroalgae/shared
cd ~/code/nordicmicroalgae
git clone https://github.com/nordicmicroalgae/backend.git
git clone https://github.com/nordicmicroalgae/content.git shared/content
```

Create postgres user and database:

```
createuser nordicmicroalgae -P -s
createdb -U nordicmicroalgae -E utf8 -O nordicmicroalgae -T template0
```

Create a `shared/config/environment.yaml` file containing:

```
debug: true
secret_key: <REPLACE-WITH-SOMETHING-RANDOM>
allowed_hosts: localhost 127.0.0.1
database_name: nordicmicroalgae
database_user: nordicmicroalgae
database_password: <REPLACE-WITH-DATABASE-PASSWORD>
```

Create directory for user-contributed images (optional):

```
mkdir shared/media
```

Create and activate virtual environment:

```
python -m venv venv --upgrade-deps
source venv/bin/activate
```

Install Python dependencies:

```
python -m pip install -r backend/requirements.txt
```

Setup and populate database:

```
python backend/manage.py migrate
python backend/manage.py importtaxa
python backend/manage.py importsynonyms
python backend/manage.py importfacts
```

Create Django admin superuser (optional):

```
python backend/manage.py createsuperuser
```

Start the development server:

```
python backend/manage.py runserver 5000
```

Open http://localhost:5000/api/ or http://localhost:5000/admin/
# Nordic Microalgae: Backend

![CI/CD status](https://github.com/nordicmicroalgae/backend/actions/workflows/main.yml/badge.svg)

This repository contains source code for the backend used in Nordic Microalgae.

The backend consists of a REST API and administration interface and is written in Python and uses, as of writing, the
latest <abbr title="Long Term Support">LTS</abbr> version (5.2) of Django as web framework.  PostgreSQL is used as
database layer and JSONB is being used heavily to store generated information in read-only tables, as well as for storing
metadata in some of the user-writable tables.

## Install and run locally

### Required repositories and folders
Clone backend into a dedicated `nordicmicroalgae` directory:
```
mkdir nordicmicroalgae
cd nordicmicroalgae
git clone https://github.com/nordicmicroalgae/backend.git
```

Create a `nordicmicroalgae/shared` directory:
```commandline
mkdir shared
```

Clone content into the shared directory:
```commandline
cd shared
git clone https://github.com/nordicmicroalgae/content.git
```

Optionally, create `nordicmicroalgae/shared/media` directory for user-contributed images:
```commandline
mkdir media
```

### Postgres database
#### Option 1: Local database
Create postgres user:
```commandline
createuser nordicmicroalgae -P -s
```

Create database:

```commandline
createdb -U nordicmicroalgae -E utf8 -O nordicmicroalgae -T template0
```

#### Option 2: Database in container
Create the container (here using podman and a local registry):
```commandline
podman run -d --name pg-local \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql \
  r-imageregistry.smhi.se/public/postgres:18-alpine
```

Create postgres user:
```commandline
podman exec -it pg-local createuser -P -s nordicmicroalgae
```

Create database: 
```commandline
podman exec -it \
  pg-local createdb \
  -e PGPASSWORD=postgres \
  -U nordicmicroalgae \
  -E utf8 \
  -O nordicmicroalgae \
  -T template0 \
  nordicmicroalgae
```

### Create configuration
Create a `nordicmicroalgae/shared/config/environment.yaml` file containing:

```yaml
debug: true
secret_key: <REPLACE-WITH-SOMETHING-RANDOM>
allowed_hosts: localhost 127.0.0.1
database_name: nordicmicroalgae
database_user: nordicmicroalgae
database_password: <REPLACE-WITH-DATABASE-PASSWORD>
```

All supported keys, with their defaults when omitted:

| Key | Default | Description |
|---|---|---|
| `secret_key` | – | Django secret key (required) |
| `debug` | `no` | Debug mode (`yes`/`true`/`on` to enable) |
| `allowed_hosts` | `.nordicmicroalgae.org` | Space-separated list of allowed host names |
| `database_name` | – | Database name |
| `database_user` | – | Database user |
| `database_password` | – | Database password |
| `database_host` | `127.0.0.1` | Database host |
| `database_port` | `5432` | Database port |
| `media_url` | `/media/` | Public URL for contributed images |
| `default_from_email` | `webmaster@localhost` | Sender address for outgoing e-mail |
| `email_host` | `localhost` | SMTP server |
| `email_port` | `25` | SMTP port |
| `email_host_user` | (empty) | SMTP user name |
| `email_host_password` | (empty) | SMTP password |
| `email_use_tls` | `no` | Use STARTTLS |
| `email_use_ssl` | `no` | Use implicit TLS |

Each key can also be set with an environment variable named `DJANGO_` followed by the key in upper case (e.g.
`DJANGO_DATABASE_PASSWORD`). Environment variables take precedence over the file. The location of the `shared`
directory can be changed with `NORDICMICROALGAE_DATA_DIR`.

### Setup Django application
Install uv by following instructions for your platform in [the official documentation](https://docs.astral.sh/uv/).

With uv, all python dependencies (including Python itself) is handled automatically when needed. Just make sure to run
the app from within its directory (`nordicmicroalgae/backend`).

#### Setup and populate database:

```commandline
uv run manage.py migrate
uv run manage.py importtaxa
uv run manage.py importsynonyms
uv run manage.py importfacts
```

Create Django admin superuser (optional):

```commandline
uv run manage.py createsuperuser
```

Start the development server:

```commandline
uv run manage.py runserver 5000
```

Open http://localhost:5000/api/ or http://localhost:5000/admin/

### Development extras
There is a project configuration for [pre-commit](https://pre-commit.com/) in the project root. This tool runs formatting
and linting checks (using ruff) every time you commit but only if you activate it for this specific repository.

Activate pre-commit by running:
```commandline
uv run pre-commit install
```

To commit without running checks (e.g. WIP commits):
```commandline
git commit --no-verify
```

## Deployment
Deployment is done by GitHub Actions (see `.github/workflows/`):

- Push to `next` deploys to staging (https://next.nordicmicroalgae.org/).
- Pushing a tag deploys to production (https://nordicmicroalgae.org/) and creates a GitHub release. By convention, tags
  are only created on `master`.

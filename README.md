# Ensimpl
===================

This is a python package that makes it simple to use
[Ensembl](http://www.ensembl.org/) data.

# To Setup
Run docker compose to start the server, to run in the background use the `-d` flag.
```bash
docker compose up -d --build
```

# Create the database
The configuration file is located in `ensimpl/config/ensimpl.ensembl.conf`. Add more rows to add more databases.
```bash
docker compose exec ensimpl python3 /app/ensimpl/cli.py create -v -d /data
```

## Project Structure

- `README.md` - This file.
- `DEV.md` - Development notes and guidelines.
- `docker-compose.yml` & `Dockerfile` - Docker configuration for container setup.
- `requirements.txt` - List of Python dependencies.
- `setup.py` - Setup script for the project installation.

### `ensimpl/`

- `__init__.py`, `utils.py`, `main.py`, `fastapi_utils.py`, `cli.py` - Core application and CLI setup.
- `db/` - Database interaction modules.
- `routers/` - API routing.
- `static/` & `templates/` - Front-end assets and HTML templates.
- `config/` - Configuration files.

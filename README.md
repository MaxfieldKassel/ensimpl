# Ensimpl
===================

This is a python package that makes it simple to use
[Ensembl](http://www.ensembl.org/) data.

# To Setup
Run docker compose to start the server, to run in the background use the `-d` flag.
```bash
docker compose up -d 
```

# Create the database
The configuration file is located in `ensimpl/config/ensimpl.ensembl.conf`. Add more rows to add more databases.
```bash
docker compose exec ensimpl python3 cli.py create
```
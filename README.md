# Atlassian Add-On
This is the Atlassian Add-On used in Fluendo Jira and Confluence instances

## System dependencies
Python 2.7

## Development
Install poetry
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Install pre-commit hooks
```
poetry run pre-commit install
```

Run docker compose to launch the local development instances
In order to access the Fluendo Web project you need to launch such services too

```
docker-compose -f docker-compose-local.yaml --env-file .env.local up
```


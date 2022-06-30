FROM python:2.7-slim

# To avoid any interactive question
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTCODE=1
RUN apt-get update
RUN apt-get install -y git build-essential supervisor
RUN rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
COPY src /app/src
COPY nginx /app/nginx
COPY supervisor /app/supervisor
COPY supervisor/app.conf /etc/supervisor/conf.d/app.conf

WORKDIR /app
RUN pip install poetry

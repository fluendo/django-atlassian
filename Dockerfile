FROM python:2.7-slim

# To avoid any interactive question
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTCODE=1
RUN apt-get update
RUN apt-get install -y git
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install poetry

FROM python:2.7-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTCODE=1
RUN apt-get update && apt-get install -y build-essential \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    git
WORKDIR /app
COPY . .
RUN pip install --upgrade pip --user
RUN pip install -r requirements.txt --user

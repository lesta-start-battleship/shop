FROM python:3.11-slim as build

WORKDIR /code

RUN apt-get update \
        && apt-get install -y --no-install-recommends gcc libpq-dev \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .

RUN pip install --upgrade pip \
        && pip install --prefix=/install -r requirements.txt


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN apt-get update \
        && apt-get install -y --no-install-recommends postgresql-client \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

COPY --from=build /install /usr/local
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


CMD ["gunicorn", "service.wsgi:application", "--bind", "0.0.0.0:8000"]

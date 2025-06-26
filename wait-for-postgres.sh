#!/bin/sh

set -e

host="$1"

until pg_isready -h "$host"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"
exec "$@"

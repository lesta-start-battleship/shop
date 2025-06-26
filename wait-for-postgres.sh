#!/bin/sh

set -e

host="$1"
shift
until pg_isready -h "$host" -p 5432; do
  echo "$host:5432 - no response"
  sleep 1
done

echo "$host:5432 - accepting connections"
exec "$@"

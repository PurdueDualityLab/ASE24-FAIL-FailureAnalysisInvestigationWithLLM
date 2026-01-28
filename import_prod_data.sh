#!/bin/bash
# Script to import data into the local postgres container
# Usage: ./import_prod_data.sh [dump_file]

DUMP_FILE=${1:-prod_dump.sql}

if [ ! -f "$DUMP_FILE" ]; then
    echo "Dump file $DUMP_FILE not found!"
    exit 1
fi

echo "Importing $DUMP_FILE into failures_local_postgres_data volume..."

# 1. Ensure local postgres container is running
LOCAL_CONTAINER=$(docker ps -q -f name=failures_local_postgres)
if [ -z "$LOCAL_CONTAINER" ]; then
    echo "Local Postgres container is not running. Starting it..."
    docker compose -f local.yml up -d postgres
    sleep 5
fi

# 2. Reset local DB (optional, but recommended to avoid conflicts)
echo "Dropping and recreating local database..."
docker compose -f local.yml exec -T postgres dropdb -U QeuwHCqzpGiWtlUXVgIHfBivAHBWklog --if-exists failures
docker compose -f local.yml exec -T postgres createdb -U QeuwHCqzpGiWtlUXVgIHfBivAHBWklog failures

# 3. Import the data
cat "$DUMP_FILE" | docker compose -f local.yml exec -T postgres psql -U QeuwHCqzpGiWtlUXVgIHfBivAHBWklog failures

if [ $? -eq 0 ]; then
    echo "Successfully imported data!"
    echo "Now running migrations to ensure schema is up to date..."
    docker compose -f local.yml run --rm django python manage.py migrate
else
    echo "Import failed!"
fi

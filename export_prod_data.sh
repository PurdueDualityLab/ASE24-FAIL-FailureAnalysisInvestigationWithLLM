#!/bin/bash
# Script to export data from the production postgres container
# Usage: ./export_prod_data.sh

echo "Exporting data from production_postgres_data volume..."

# 1. Check if the production postgres container is running
PROD_CONTAINER=$(docker ps -q -f name=failures_production_postgres)
if [ -z "$PROD_CONTAINER" ]; then
    echo "Production Postgres container is not running. Starting it..."
    docker compose -f production.yml up -d postgres
    sleep 5 # Wait for it to start
fi

# 2. Dump the data
docker compose -f production.yml exec -T postgres pg_dump -U QeuwHCqzpGiWtlUXVgIHfBivAHBWklog failures > prod_dump.sql

if [ $? -eq 0 ]; then
    echo "Successfully exported to prod_dump.sql"
    echo "You can now import this into your local environment."
else
    echo "Export failed!"
fi

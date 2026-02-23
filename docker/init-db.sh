#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# PostgreSQL init script
# Runs once on first container start (postgres docker entrypoint convention).
# Reads per-app credentials from environment variables injected via .env
# and creates a dedicated user + database for each app.
#
# Variable convention (one set per app):
#   <APP>_DB_USER     – the role to create
#   <APP>_DB_PASSWORD – the role's password
#   <APP>_DB_NAME     – the database to create and grant to the role
#
# Currently configured apps: APP
# ---------------------------------------------------------------------------

create_app_db() {
	local user="$1"
	local password="$2"
	local dbname="$3"

	echo "  -> ensuring role '${user}' exists"
	psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-SQL
		        DO \$\$
		        BEGIN
		            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${user}') THEN
		                CREATE ROLE "${user}" WITH LOGIN PASSWORD '${password}';
		            ELSE
		                ALTER ROLE "${user}" WITH PASSWORD '${password}';
		            END IF;
		        END
		        \$\$;
	SQL

	echo "  -> ensuring database '${dbname}' exists"
	psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-SQL
		        SELECT 'CREATE DATABASE "${dbname}" OWNER "${user}"'
		        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${dbname}')
		        \gexec
	SQL

	echo "  -> granting privileges on '${dbname}' to '${user}'"
	psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${dbname}" <<-SQL
		        GRANT ALL PRIVILEGES ON DATABASE "${dbname}" TO "${user}";
		        GRANT ALL ON SCHEMA public TO "${user}";
	SQL

	echo "  -> done: ${user}@${dbname}"
}

echo "=== init-db.sh: creating application databases ==="

# --- backend app ---
: "${APP_DB_USER:?APP_DB_USER is not set in .env}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is not set in .env}"
: "${APP_DB_NAME:?APP_DB_NAME is not set in .env}"
create_app_db "${APP_DB_USER}" "${APP_DB_PASSWORD}" "${APP_DB_NAME}"

# --- zitadel ---
: "${ZITADEL_DB_USER:?ZITADEL_DB_USER is not set in .env}"
: "${ZITADEL_DB_PASSWORD:?ZITADEL_DB_PASSWORD is not set in .env}"
: "${ZITADEL_DB_NAME:?ZITADEL_DB_NAME is not set in .env}"
create_app_db "${ZITADEL_DB_USER}" "${ZITADEL_DB_PASSWORD}" "${ZITADEL_DB_NAME}"

echo "=== init-db.sh: finished ==="

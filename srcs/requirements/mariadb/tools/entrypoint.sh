#!/bin/sh
set -eu

DB_ROOT_PASSWORD="$(cat /run/secrets/db_root_password)"
DB_PASSWORD="$(cat /run/secrets/db_password)"

mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld

if [ ! -d /var/lib/mysql/mysql ]; then
    echo "[mariadb] empty data directory -> first-time initialisation"

    mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db >/dev/null

    mariadbd --user=mysql --bootstrap <<EOSQL
USE mysql;
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASSWORD}';
DELETE FROM mysql.global_priv WHERE User = '';
DROP DATABASE IF EXISTS test;
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
EOSQL

    if [ ! -d "/var/lib/mysql/${MYSQL_DATABASE}" ]; then
        echo "[mariadb] FATAL: database '${MYSQL_DATABASE}' was not created" >&2
        exit 1
    fi

    echo "[mariadb] initialisation done: database '${MYSQL_DATABASE}', user '${MYSQL_USER}'"
else
    echo "[mariadb] existing data directory found -> skipping initialisation"
fi

echo "[mariadb] starting daemon as PID 1"
exec "$@"

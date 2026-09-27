#!/bin/sh
set -eu

WP_PATH=/var/www/html

DB_PASSWORD="$(cat /run/secrets/db_password)"
WP_ADMIN_PASSWORD="$(cat /run/secrets/wp_admin_password)"
WP_USER_PASSWORD="$(cat /run/secrets/wp_user_password)"

wp_run() { wp --allow-root --path="$WP_PATH" "$@"; }

echo "[wordpress] waiting for ${MYSQL_HOST}:3306 ..."
i=0
until mariadb-admin ping --host="$MYSQL_HOST" --user="$MYSQL_USER" \
                         --password="$DB_PASSWORD" --silent 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge 60 ]; then
        echo "[wordpress] database unreachable after 60s - aborting" >&2
        exit 1
    fi
    sleep 1
done
echo "[wordpress] database is up"

if [ ! -f "$WP_PATH/wp-config.php" ]; then
    echo "[wordpress] no wp-config.php -> installing WordPress"

    wp_run core download --version=6.7.1 --force

    wp_run config create \
        --dbname="$MYSQL_DATABASE" \
        --dbuser="$MYSQL_USER" \
        --dbpass="$DB_PASSWORD" \
        --dbhost="$MYSQL_HOST" \
        --dbcharset=utf8mb4 \
        --skip-check



    wp_run config set FORCE_SSL_ADMIN true --raw --type=constant
    wp_run config set WP_HOME "$WP_URL" --type=constant
    wp_run config set WP_SITEURL "$WP_URL" --type=constant

    wp_run core install \
        --url="$WP_URL" \
        --title="$WP_TITLE" \
        --admin_user="$WP_ADMIN_USER" \
        --admin_password="$WP_ADMIN_PASSWORD" \
        --admin_email="$WP_ADMIN_EMAIL" \
        --skip-email


    wp_run user create "$WP_USER" "$WP_USER_EMAIL" \
        --role=author \
        --user_pass="$WP_USER_PASSWORD"

    echo "[wordpress] installation complete"
else
    echo "[wordpress] existing installation found -> skipping install"
fi

if [ -n "${REDIS_HOST:-}" ]; then
    echo "[wordpress] REDIS_HOST=${REDIS_HOST} -> enabling the redis object cache"
    wp_run config set WP_REDIS_HOST "$REDIS_HOST" --type=constant
    wp_run config set WP_REDIS_PORT "${REDIS_PORT:-6379}" --raw --type=constant
    wp_run config set WP_CACHE true --raw --type=constant

    if ! wp_run plugin is-installed redis-cache 2>/dev/null; then
        wp_run plugin install redis-cache
    fi
    wp_run plugin activate redis-cache


    wp_run redis enable || echo "[wordpress] warning: could not enable redis cache"
fi

mkdir -p /run/php
chown -R www-data:www-data "$WP_PATH"

echo "[wordpress] starting php-fpm as PID 1"
exec "$@"

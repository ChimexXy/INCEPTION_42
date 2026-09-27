#!/bin/sh
set -eu

SSL_DIR=/etc/nginx/ssl
CRT="$SSL_DIR/inception.crt"
KEY="$SSL_DIR/inception.key"

envsubst '${DOMAIN_NAME}' \
    < /etc/nginx/templates/default.conf \
    > /etc/nginx/conf.d/default.conf

if [ "${ENABLE_BONUS:-0}" = "1" ]; then
    echo "[nginx] ENABLE_BONUS=1 -> adding the bonus sub-domains"
    envsubst '${DOMAIN_NAME}' \
        < /etc/nginx/templates/bonus.conf \
        > /etc/nginx/conf.d/bonus.conf
else
    rm -f /etc/nginx/conf.d/bonus.conf
fi

if [ ! -f "$CRT" ] || [ ! -f "$KEY" ]; then
    echo "[nginx] generating a self-signed certificate for ${DOMAIN_NAME}"
    mkdir -p "$SSL_DIR"

    openssl req -x509 -nodes -newkey rsa:2048 -sha256 -days 365 \
        -keyout "$KEY" -out "$CRT" \
        -subj "/C=MA/ST=Khouribga/L=Khouribga/O=42/OU=1337/CN=${DOMAIN_NAME}" \
        -addext "subjectAltName=DNS:${DOMAIN_NAME},DNS:*.${DOMAIN_NAME}" \
        2>/dev/null
    chmod 600 "$KEY"
fi

nginx -t
echo "[nginx] starting as PID 1 on :443"
exec "$@"

FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        php8.2-cli \
        php8.2-mysql \
        curl \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ARG ADMINER_VERSION=4.8.1
RUN mkdir -p /var/www/adminer \
 && curl -fsSL -o /var/www/adminer/index.php \
      "https://github.com/vrana/adminer/releases/download/v${ADMINER_VERSION}/adminer-${ADMINER_VERSION}.php" \
 && chown -R www-data:www-data /var/www/adminer

WORKDIR /var/www/adminer
EXPOSE 8080
USER www-data

CMD ["php", "-S", "0.0.0.0:8080", "-t", "/var/www/adminer"]

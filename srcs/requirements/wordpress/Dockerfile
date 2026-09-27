FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        php8.2-fpm \
        php8.2-mysql \
        php8.2-redis \
        php8.2-mbstring \
        php8.2-xml \
        php8.2-gd \
        php8.2-curl \
        php8.2-zip \
        mariadb-client \
        curl \
        ca-certificates \
        less \
 && rm -rf /var/lib/apt/lists/*

ARG WP_CLI_VERSION=2.11.0
RUN curl -fsSL -o /usr/local/bin/wp \
      "https://github.com/wp-cli/wp-cli/releases/download/v${WP_CLI_VERSION}/wp-cli-${WP_CLI_VERSION}.phar" \
 && chmod +x /usr/local/bin/wp \
 && wp --allow-root --version

COPY conf/wordpress.conf /etc/php/8.2/fpm/pool.d/www.conf
COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && mkdir -p /run/php /var/www/html \
 && chown -R www-data:www-data /var/www/html

WORKDIR /var/www/html
EXPOSE 9000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["php-fpm8.2", "-F"]

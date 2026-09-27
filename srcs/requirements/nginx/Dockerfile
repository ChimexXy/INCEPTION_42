FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        nginx \
        openssl \
        gettext-base \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/nginx/sites-enabled/default \
 && rm -rf /var/www/html/*

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log

COPY conf/nginx.conf       /etc/nginx/templates/default.conf
COPY conf/nginx_bonus.conf /etc/nginx/templates/bonus.conf

COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && mkdir -p /etc/nginx/ssl

EXPOSE 443

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

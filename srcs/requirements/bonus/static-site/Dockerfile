FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/nginx/sites-enabled/default \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log

COPY conf/static.conf /etc/nginx/conf.d/static.conf
COPY site/ /var/www/static/

RUN chown -R www-data:www-data /var/www/static

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

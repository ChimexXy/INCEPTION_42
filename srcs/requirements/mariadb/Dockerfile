FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        mariadb-server \
        mariadb-client \
 && rm -rf /var/lib/apt/lists/*

RUN rm -rf /var/lib/mysql/* && chown mysql:mysql /var/lib/mysql

COPY conf/mariadb.cnf /etc/mysql/mariadb.conf.d/99-inception.cnf

COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 3306

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["mariadbd", "--user=mysql"]

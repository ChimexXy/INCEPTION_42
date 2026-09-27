
# Developer documentation

This document describes the implementation and development workflow for the current Inception project. User operations are in USER_DOC.md.

## 1. Repository layout

~~~text
.
├── Makefile
├── README.md
├── USER_DOC.md
├── DEV_DOC.md
├── TESTING_ROADMAP.md
├── secrets/
└── srcs/
    ├── .env
    ├── docker-compose.yml
    ├── docker-compose.bonus.yml
    └── requirements/
        ├── nginx/
        ├── wordpress/
        ├── mariadb/
        └── bonus/
            ├── redis/
            ├── ftp/
            ├── adminer/
            ├── static-site/
            └── status/
~~~

The mandatory Compose file defines exactly three services: nginx, wordpress and mariadb.

The bonus Compose file is an overlay. It adds Redis, FTP, Adminer, the static site and the status service, and changes the WordPress/NGINX environment for bonus behavior.

## 2. Makefile

The current Makefile defines:

| Target | Purpose |
|---|---|
| make | setup + build + start mandatory stack |
| make bonus | setup + build + start mandatory + bonus |
| make setup | create data directories and missing secrets |
| make dirs | create WordPress and MariaDB data directories |
| make secrets | generate missing secret files |
| make down | stop and remove Compose containers |
| make clean | down + remove project images + remove generated secrets |
| make fclean | clean + remove project volumes + invoke DATA_PATH cleanup |
| make re | fclean then mandatory make |

There are currently no make test, make test-bonus, make ps, make logs, make build, make build-bonus, make hosts or make help targets.

Use Docker and Compose commands directly for inspection and testing.

The Makefile currently reads DATA_PATH and DOMAIN_NAME from srcs/.env with sed.

## 3. Environment and secrets

### srcs/.env

This file contains non-sensitive configuration:

- login and domain;
- persistent data path;
- MariaDB host, database and user;
- WordPress URL, title, users and e-mail addresses;
- Redis host/port for the bonus;
- FTP user and passive-port settings for the bonus.

Passwords are not stored there.

### secrets/

The Makefile generates these local files when they are missing:

~~~text
db_root_password.txt
db_password.txt
wp_admin_password.txt
wp_user_password.txt
ftp_password.txt
~~~

The files are git-ignored. Compose mounts them as Docker secrets under /run/secrets/.

## 4. Mandatory Compose architecture

### NGINX

- custom image;
- host port 443 published;
- shared WordPress volume mounted at /var/www/html;
- environment contains DOMAIN_NAME;
- renders the virtual-host template at startup;
- optionally renders the bonus virtual hosts;
- creates a self-signed certificate when required;
- checks the generated NGINX configuration with nginx -t;
- runs NGINX in the foreground.

### WordPress

- custom image;
- PHP-FPM 8.2;
- listens internally on 0.0.0.0:9000;
- shared WordPress volume;
- waits for healthy MariaDB through Compose dependency conditions;
- performs first installation with WP-CLI;
- reads passwords from Docker secrets;
- enables Redis integration only when the bonus environment is provided;
- runs php-fpm8.2 -F as the main process.

### MariaDB

- custom image;
- MariaDB server from Debian Bookworm packages;
- no host port published;
- data stored in the MariaDB named volume;
- healthcheck uses mariadb-admin ping through the MariaDB socket;
- initializes the database and application user only for a fresh data directory;
- runs mariadbd in the foreground.

## 5. Build and startup sequence

A normal mandatory start is:

~~~bash
make
~~~

The effective Compose command is:

~~~bash
docker compose -f srcs/docker-compose.yml up -d --build
~~~

The bonus command uses both files:

~~~bash
docker compose -f srcs/docker-compose.yml -f srcs/docker-compose.bonus.yml up -d --build
~~~

The dependency order is:

~~~text
MariaDB
  -> healthcheck passes
  -> WordPress can start its initialization
  -> NGINX provides the HTTPS entry point
~~~

NGINX depends on the WordPress service, while WordPress depends on a healthy MariaDB service.

## 6. Entrypoints and PID 1

The custom entrypoints prepare the container and then use exec for the final daemon.

Conceptually:

~~~text
entrypoint shell
    |
    +-- setup / initialization
    |
    +-- exec daemon
             |
             +-- daemon becomes PID 1
~~~

This is important for signal handling and clean shutdown.

Do not replace the real foreground process with commands such as:

~~~text
tail -f /dev/null
sleep infinity
while true; do ...; done
~~~

For correction, be able to explain why the service process needs to remain in the foreground and why exec is used.

## 7. NGINX and TLS

The NGINX entrypoint:

1. renders the main vhost using DOMAIN_NAME;
2. renders bonus vhosts when ENABLE_BONUS=1;
3. removes the bonus configuration in mandatory-only mode;
4. creates the self-signed certificate when missing;
5. runs nginx -t;
6. executes the foreground NGINX command.

The mandatory host mapping is:

~~~text
host 443 -> nginx 443
~~~

Port 80 is not published.

## 8. WordPress and PHP-FPM

NGINX does not execute PHP itself.

The request path is:

~~~text
Browser
  |
  | HTTPS
  v
NGINX
  |
  | FastCGI :9000
  v
PHP-FPM / WordPress
  |
  | SQL
  v
MariaDB
~~~

PHP-FPM is configured in srcs/requirements/wordpress/conf/wordpress.conf.

The WordPress entrypoint uses a bounded retry loop for MariaDB. On a fresh volume it:

- downloads WordPress with WP-CLI;
- creates wp-config.php;
- sets the site URL;
- installs WordPress;
- creates the second user;
- optionally enables Redis;
- starts PHP-FPM.

When wp-config.php already exists, the initial installation is skipped.

## 9. MariaDB initialization

The MariaDB Dockerfile removes the package-created contents of /var/lib/mysql so a new mounted volume starts empty.

The entrypoint then:

1. creates /run/mysqld;
2. initializes the data directory with mariadb-install-db;
3. runs a bootstrap SQL batch;
4. sets the root password;
5. creates the WordPress database;
6. creates the WordPress database user;
7. grants privileges;
8. verifies that the database directory was created;
9. starts mariadbd.

An existing initialized volume is reused rather than reinitialized.

## 10. Volumes and persistence

The project uses two named volumes with local-driver bind-style storage:

~~~yaml
volumes:
  wordpress_files:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/mozahnou/data/wordpress
~~~

and the equivalent MariaDB volume.

The important distinction is that the Docker object is still a named volume:

~~~text
inception_wordpress_files
inception_mariadb_data
~~~

while the backing data is stored under:

~~~text
/home/mozahnou/data/wordpress
/home/mozahnou/data/mariadb
~~~

Verify the real configuration with:

~~~bash
docker volume inspect inception_wordpress_files
docker volume inspect inception_mariadb_data
~~~

## 11. Network

The project defines a user-created bridge network named inception.

Services communicate using Docker DNS:

~~~text
wordpress -> mariadb:3306
wordpress -> redis:6379       # bonus
adminer   -> mariadb:3306     # bonus
~~~

Do not replace this with host networking or legacy links.

## 12. Bonus overlay

Run the bonus with both Compose files:

~~~bash
docker compose -f srcs/docker-compose.yml -f srcs/docker-compose.bonus.yml up -d --build
~~~

The overlay adds:

- redis;
- ftp;
- adminer;
- static-site;
- status.

It also provides ENABLE_BONUS=1 to NGINX and REDIS_HOST/REDIS_PORT to WordPress.

### Bonus port behavior

Web-based bonus services remain behind NGINX.

FTP publishes:

~~~text
host 21 -> ftp 21
host 21000-21010 -> ftp 21000-21010
~~~

because FTP is not an HTTP service and needs its own control/data channels.

## 13. Development workflow

### Change a Dockerfile or service configuration

Rebuild the affected service:

~~~bash
docker compose -f srcs/docker-compose.yml build <service>
docker compose -f srcs/docker-compose.yml up -d <service>
~~~

For a bonus service, include docker-compose.bonus.yml in the command.

### Change srcs/.env

Recreate the affected containers:

~~~bash
docker compose -f srcs/docker-compose.yml up -d --force-recreate
~~~

### Change WordPress installation logic

Because the initialization is intentionally one-time, test changes with fresh data:

~~~bash
make fclean
make
~~~

## 14. Debugging commands

Containers:

~~~bash
docker ps
docker inspect <container>
docker logs <container>
~~~

Compose:

~~~bash
docker compose -f srcs/docker-compose.yml ps
docker compose -f srcs/docker-compose.yml config
docker compose -f srcs/docker-compose.yml config --services
~~~

Network:

~~~bash
docker network inspect inception
docker exec wordpress getent hosts mariadb
~~~

Volumes:

~~~bash
docker volume ls --filter name=inception
docker volume inspect inception_wordpress_files
docker volume inspect inception_mariadb_data
~~~

WordPress:

~~~bash
docker exec wordpress wp --allow-root --path=/var/www/html user list
docker exec wordpress wp --allow-root --path=/var/www/html option get siteurl
docker exec wordpress wp --allow-root --path=/var/www/html db check
~~~

MariaDB:

~~~bash
docker inspect mariadb --format '{{.State.Health.Status}}'
docker exec mariadb mariadb-admin ping --socket=/run/mysqld/mysqld.sock
~~~

TLS:

~~~bash
curl -kI https://mozahnou.42.fr
openssl s_client -connect mozahnou.42.fr:443 -tls1_2
openssl s_client -connect mozahnou.42.fr:443 -tls1_3
~~~

## 15. Defense checklist

For every subject requirement, know:

1. **Where** it is implemented.
2. **How** to demonstrate it.
3. **Why** it is designed that way.

Core subjects:

- Docker image versus container;
- Dockerfile versus Compose;
- Docker versus virtual machine;
- bridge network and service-name DNS;
- named volumes versus bind mounts;
- persistence;
- Docker secrets versus environment variables;
- NGINX and TLS;
- FastCGI and PHP-FPM;
- MariaDB initialization;
- PID 1 and exec;
- restart/dependency behavior;
- mandatory versus bonus separation.

The complete practical test sequence is in TESTING_ROADMAP.md.

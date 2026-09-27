
# Inception

*This project has been created as part of the 42 curriculum by mozahnou.*

## 1. Project overview

Inception builds a small web infrastructure with Docker Compose. The mandatory part contains exactly three services:

- **NGINX**: the only public HTTPS entry point.
- **WordPress + PHP-FPM**: the application container; it does not contain a web server.
- **MariaDB**: the database container; it is reachable only through the Docker network.

The bonus overlay adds Redis, FTP, Adminer, a static showcase site and a status service.

The mandatory stack can be built and evaluated independently from the bonus.

## 2. Architecture

~~~text
Host :443
    |
    v
+-------------------------------+
| NGINX                         |
| TLS 1.2 / TLS 1.3             |
| FastCGI                       |
+---------------+---------------+
                |
                v
+-------------------------------+
| WordPress + PHP-FPM :9000    |
+---------------+---------------+
                |
                v
+-------------------------------+
| MariaDB :3306                 |
+-------------------------------+

Docker network: inception

Persistent named volumes:
  inception_wordpress_files -> /home/mozahnou/data/wordpress
  inception_mariadb_data   -> /home/mozahnou/data/mariadb
~~~

For the bonus, the web services are reached through NGINX subdomains. FTP publishes its own protocol ports because it is not HTTP.

## 3. Services

| Part | Service | Role | Host port |
|---|---|---|---|
| Mandatory | nginx | TLS termination and reverse proxy / FastCGI gateway | 443 |
| Mandatory | wordpress | WordPress with PHP-FPM | none |
| Mandatory | mariadb | WordPress database | none |
| Bonus | redis | WordPress object cache | none |
| Bonus | ftp | FTP access to WordPress files | 21, 21000-21010 |
| Bonus | adminer | Database administration UI | none |
| Bonus | static-site | Static HTML/CSS/JS showcase | none |
| Bonus | status | Service status page | none |

The mandatory setup does not publish MariaDB port 3306 or PHP-FPM port 9000 to the host.

## 4. Repository structure

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

Each service has its own Dockerfile and configuration.

## 5. Configuration and secrets

Non-sensitive settings are kept in srcs/.env:

~~~text
LOGIN=mozahnou
DOMAIN_NAME=mozahnou.42.fr
DATA_PATH=/home/mozahnou/data

MYSQL_HOST=mariadb
MYSQL_DATABASE=wordpress
MYSQL_USER=wp_user

WP_TITLE=Inception
WP_URL=https://mozahnou.42.fr
WP_ADMIN_USER=site_owner
WP_ADMIN_EMAIL=site_owner@mozahnou.42.fr
WP_USER=mozahnou_editor
WP_USER_EMAIL=editor@mozahnou.42.fr
~~~

The project also defines the bonus Redis and FTP settings in the same file.

Passwords are kept in secrets/ and supplied to containers as Docker secrets under /run/secrets/.

## 6. Running the project

From the repository root:

### Mandatory

~~~bash
make
~~~

### Bonus

~~~bash
make bonus
~~~

### Stop

~~~bash
make down
~~~

This removes the project containers while preserving images, named volumes and persistent data.

### Clean

~~~bash
make clean
~~~

This also removes the project images and the generated secret files. The named volumes remain.

### Full cleanup

~~~bash
make fclean
~~~

This performs the clean step, removes the two project volumes and invokes the project cleanup for DATA_PATH. Treat it as destructive.

### Rebuild

~~~bash
make re
~~~

This is fclean followed by a fresh mandatory build.

## 7. Host name setup

The current Makefile does not edit /etc/hosts.

For the mandatory site:

~~~bash
sudo sh -c 'printf "127.0.0.1 mozahnou.42.fr\n" >> /etc/hosts'
~~~

For the bonus, also add:

~~~bash
sudo sh -c 'printf "127.0.0.1 static.mozahnou.42.fr adminer.mozahnou.42.fr status.mozahnou.42.fr\n" >> /etc/hosts'
~~~

Then check:

~~~bash
getent hosts mozahnou.42.fr
~~~

## 8. Access

Mandatory:

~~~text
https://mozahnou.42.fr
https://mozahnou.42.fr/wp-admin
~~~

The project uses a locally generated self-signed certificate, so a browser warning is expected.

Bonus:

~~~text
https://static.mozahnou.42.fr
https://adminer.mozahnou.42.fr
https://status.mozahnou.42.fr

FTP:
  host: mozahnou.42.fr
  port: 21
  passive ports: 21000-21010
~~~

## 9. Persistence

The project uses two named Docker volumes backed by the required host locations:

| Named volume | Container path | Host data |
|---|---|---|
| inception_wordpress_files | /var/www/html | /home/mozahnou/data/wordpress |
| inception_mariadb_data | /var/lib/mysql | /home/mozahnou/data/mariadb |

The data must survive container restart and make down.

## 10. Important design choices

### One service per container

Each service has its own container and runs its main process in the foreground.

### PID 1 and exec

Entrypoints finish by using exec so the real daemon becomes PID 1 and receives Docker signals directly.

### User-defined network

The inception bridge network provides service-name DNS, for example:

~~~text
wordpress -> mariadb:3306
wordpress -> redis:6379      # bonus
adminer   -> mariadb:3306    # bonus
~~~

No host networking or legacy links mechanism is used.

### TLS

NGINX terminates TLS and accepts TLS 1.2 and TLS 1.3.

### PHP-FPM

NGINX sends PHP requests to WordPress through FastCGI. PHP-FPM listens internally on port 9000.

### Initialization

MariaDB initializes only for a fresh data directory. WordPress installs only when wp-config.php is absent. Existing data is reused after restarts.

### Secrets

Passwords are read from Docker secret files rather than being stored in the environment.

## 11. Useful verification commands

~~~bash
docker ps
docker compose -f srcs/docker-compose.yml config
docker compose -f srcs/docker-compose.yml config --services
docker network inspect inception
docker volume inspect inception_wordpress_files
docker volume inspect inception_mariadb_data
docker logs nginx
docker logs wordpress
docker logs mariadb
curl -kI https://mozahnou.42.fr
openssl s_client -connect mozahnou.42.fr:443 -tls1_2
openssl s_client -connect mozahnou.42.fr:443 -tls1_3
~~~

For the complete correction sequence, see TESTING_ROADMAP.md.

## 12. Defense topics

Be ready to explain:

- image versus container;
- Dockerfile versus Compose;
- Docker versus a virtual machine;
- bridge networking and Docker DNS;
- named volumes versus bind mounts;
- persistence;
- Docker secrets versus environment variables;
- NGINX, TLS and FastCGI;
- PHP-FPM;
- MariaDB initialization;
- PID 1 and exec;
- mandatory versus bonus separation.

For every requirement, know **where it is implemented, how to demonstrate it, and why it is designed that way**.

## 13. AI use

AI tools were used as development assistance for scaffolding, debugging and documentation. The final project must still be understood, tested and explainable by the author during the defense.

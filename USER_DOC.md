
# User documentation

This document explains how to run and use the current Inception project. Development details are in DEV_DOC.md.

## 1. Requirements

Use the project from a Linux virtual machine as required by the subject.

Check the required tools:

~~~bash
docker --version
docker compose version
make --version
openssl version
curl --version
~~~

The current user must be able to run Docker without sudo:

~~~bash
docker ps
~~~

## 2. First setup

From the repository root:

~~~bash
make
~~~

The Makefile creates the persistent data directories and generates any missing secret files before building and starting the mandatory stack.

The current Makefile does not edit /etc/hosts. Add the project hostname manually:

~~~bash
sudo sh -c 'printf "127.0.0.1 mozahnou.42.fr\n" >> /etc/hosts'
~~~

For the bonus, also add:

~~~bash
sudo sh -c 'printf "127.0.0.1 static.mozahnou.42.fr adminer.mozahnou.42.fr status.mozahnou.42.fr\n" >> /etc/hosts'
~~~

Check the result:

~~~bash
getent hosts mozahnou.42.fr
~~~

## 3. Start the project

### Mandatory

~~~bash
make
~~~

| Service | Function | Access |
|---|---|---|
| nginx | HTTPS entry point | https://mozahnou.42.fr |
| wordpress | WordPress + PHP-FPM | through NGINX |
| mariadb | database | internal Docker network only |

### Bonus

~~~bash
make bonus
~~~

| Service | Function | Access |
|---|---|---|
| redis | WordPress object cache | internal only |
| ftp | website file transfer | mozahnou.42.fr:21 |
| adminer | database administration | https://adminer.mozahnou.42.fr |
| static-site | static showcase | https://static.mozahnou.42.fr |
| status | service status page | https://status.mozahnou.42.fr |

## 4. Stop and clean

### Stop containers and preserve data

~~~bash
make down
~~~

This removes the project containers while keeping the images, named volumes and persistent data.

### Remove project images and generated secrets

~~~bash
make clean
~~~

This also removes the generated files in secrets/. The named volumes are kept.

### Full cleanup

~~~bash
make fclean
~~~

Use this only when you are ready for a clean rebuild. It removes the project containers and images, removes the two project volumes, and invokes the project's cleanup for DATA_PATH.

### Full rebuild

~~~bash
make re
~~~

## 5. WordPress

Open:

~~~text
https://mozahnou.42.fr
https://mozahnou.42.fr/wp-admin
~~~

The project creates two WordPress users:

| User | Role |
|---|---|
| site_owner | administrator |
| mozahnou_editor | author |

The first installation is automated with WP-CLI. When wp-config.php already exists in the persistent volume, the entrypoint skips the installation.

## 6. Credentials

Password files are kept in:

~~~text
secrets/db_root_password.txt
secrets/db_password.txt
secrets/wp_admin_password.txt
secrets/wp_user_password.txt
secrets/ftp_password.txt
~~~

The FTP secret is used by the bonus service.

Read a password locally when necessary:

~~~bash
cat secrets/wp_admin_password.txt
~~~

The containers receive passwords through Docker secrets mounted under /run/secrets/.

Never commit the secret files.

## 7. Adminer

Open:

~~~text
https://adminer.mozahnou.42.fr
~~~

Use:

~~~text
System:   MySQL
Server:   mariadb
Database: wordpress
User:     wp_user
Password: contents of secrets/db_password.txt
~~~

Adminer is not published directly to a host port; NGINX provides the HTTPS entry point.

## 8. FTP

The bonus FTP service uses:

~~~text
Host:     mozahnou.42.fr
Port:     21
User:     ftp_user
Password: contents of secrets/ftp_password.txt
Mode:     passive
~~~

Passive data ports are 21000 through 21010.

The FTP service shares the WordPress files, so a file uploaded through FTP can become visible to the website.

## 9. Static site and status page

Static site:

~~~text
https://static.mozahnou.42.fr
~~~

Status dashboard:

~~~text
https://status.mozahnou.42.fr
~~~

The status service also exposes:

~~~text
https://status.mozahnou.42.fr/health
~~~

## 10. Checking the containers

The current Makefile does not provide ps, logs or test targets. Use Docker directly:

~~~bash
docker ps
docker compose -f srcs/docker-compose.yml ps
docker logs nginx
docker logs wordpress
docker logs mariadb
~~~

A healthy mandatory stack should show:

~~~text
nginx       Up
wordpress   Up
mariadb     Up (healthy)
~~~

For the bonus, Redis, FTP, Adminer, static-site and status should also remain Up.

## 11. Basic functional checks

DNS:

~~~bash
getent hosts mozahnou.42.fr
~~~

HTTPS:

~~~bash
curl -kI https://mozahnou.42.fr
~~~

MariaDB health:

~~~bash
docker inspect mariadb --format '{{.State.Status}} health={{.State.Health.Status}}'
~~~

Network:

~~~bash
docker network inspect inception
~~~

Volumes:

~~~bash
docker volume inspect inception_wordpress_files
docker volume inspect inception_mariadb_data
~~~

## 12. Common problems

| Symptom | First check |
|---|---|
| ERR_NAME_NOT_RESOLVED | Check /etc/hosts and getent hosts |
| 502 Bad Gateway | docker logs wordpress |
| MariaDB is unhealthy | docker logs mariadb |
| Container keeps restarting | docker logs <container> |
| HTTPS is unreachable | docker ps and host port 443 |
| Bonus hostname fails | /etc/hosts and make bonus |
| Data disappears after rebuild | inspect the named volumes and DATA_PATH |

For the complete correction procedure, use TESTING_ROADMAP.md.

## 13. Persistent data

The project stores persistent data in:

~~~text
/home/mozahnou/data/wordpress
/home/mozahnou/data/mariadb
~~~

These locations back the named volumes:

~~~text
inception_wordpress_files
inception_mariadb_data
~~~

Removing containers does not remove this persistent data.

Do not use make fclean on a site that must be preserved.

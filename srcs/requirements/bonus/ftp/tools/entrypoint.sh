set -eu

FTP_PASSWORD="$(cat /run/secrets/ftp_password)"
FTP_ROOT=/var/www/html
grep -qx /usr/sbin/nologin /etc/shells || echo /usr/sbin/nologin >> /etc/shells

WWW_UID="$(id -u www-data)"
WWW_GID="$(id -g www-data)"

if ! id "$FTP_USER" >/dev/null 2>&1; then
    echo "[ftp] creating user ${FTP_USER} (uid ${WWW_UID}, gid ${WWW_GID})"
    useradd -M -o -u "$WWW_UID" -g "$WWW_GID" \
            -d "$FTP_ROOT" -s /usr/sbin/nologin "$FTP_USER"
fi

echo "${FTP_USER}:${FTP_PASSWORD}" | chpasswd
echo "$FTP_USER" > /etc/vsftpd.userlist

echo "[ftp] serving ${FTP_ROOT} as ${FTP_USER}, starting vsftpd as PID 1"
exec "$@"

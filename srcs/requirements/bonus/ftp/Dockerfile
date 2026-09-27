FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends vsftpd \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/run/vsftpd/empty

COPY conf/ftp.conf /etc/vsftpd.conf
COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 21 21000-21010

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["vsftpd", "/etc/vsftpd.conf"]

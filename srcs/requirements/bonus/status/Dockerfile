FROM debian:bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

COPY app/server.py /opt/status/server.py

RUN useradd --system --no-create-home --shell /usr/sbin/nologin status
USER status

EXPOSE 5000

CMD ["python3", "-u", "/opt/status/server.py"]

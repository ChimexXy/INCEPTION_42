import json
import os
import socket
import ssl
import time
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN_PORT = int(os.environ.get("STATUS_PORT", "5000"))
TIMEOUT = 2.0

CHECKS = [
    ("nginx",       "nginx",       443,  "tls",   "TLS entry point (443)"),
    ("wordpress",   "wordpress",   9000, "tcp",   "php-fpm FastCGI pool"),
    ("mariadb",     "mariadb",     3306, "mysql", "Database server"),
    ("redis",       "redis",       6379, "redis", "WordPress object cache"),
    ("ftp",         "ftp",         21,   "ftp",   "vsftpd control channel"),
    ("adminer",     "adminer",     8080, "http",  "Database administration UI"),
    ("static-site", "static-site", 3000, "http",  "Static showcase site"),
]


def _connect(host, port):
    return socket.create_connection((host, port), timeout=TIMEOUT)


def probe(host, port, kind):
    """Return (ok, detail). Never raises: a failing probe is a result, not a crash."""
    started = time.monotonic()
    try:
        if kind == "tls":
            ctx = ssl.create_default_context()
    
    
    
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with _connect(host, port) as raw:
                with ctx.wrap_socket(raw, server_hostname=host) as tls:
                    detail = tls.version()

        elif kind == "redis":
            with _connect(host, port) as sock:
                sock.sendall(b"PING\r\n")
                reply = sock.recv(64)
            if not reply.startswith(b"+PONG"):
                return False, "unexpected reply to PING"
            detail = "PONG"

        elif kind == "ftp":
            with _connect(host, port) as sock:
                banner = sock.recv(128).decode("utf-8", "replace").strip()
            if not banner.startswith("220"):
                return False, "no 220 banner"
            detail = banner[:48]

        elif kind == "mysql":
    
            with _connect(host, port) as sock:
                head = sock.recv(128)
            if len(head) < 6:
                return False, "empty handshake"
            version = head[5:].split(b"\x00", 1)[0].decode("utf-8", "replace")
            detail = version or "handshake ok"

        elif kind == "http":
            with _connect(host, port) as sock:
                sock.sendall(
                    b"GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n"
                    % host.encode()
                )
                head = sock.recv(64).decode("utf-8", "replace")
            status = head.split(" ")[1] if " " in head else "?"
            if not status.startswith(("2", "3")):
                return False, "HTTP " + status
            detail = "HTTP " + status

        else:
            with _connect(host, port):
                detail = "connected"

    except Exception as exc:                    
        return False, type(exc).__name__ + ": " + str(exc)[:60]

    return True, "%s  (%d ms)" % (detail, (time.monotonic() - started) * 1000)


def collect():
    results = []
    for name, host, port, kind, desc in CHECKS:
        ok, detail = probe(host, port, kind)
        results.append(
            {"service": name, "target": "%s:%d" % (host, port), "description": desc,
             "ok": ok, "detail": detail}
        )
    return results


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Inception &middot; status</title>
<style>
 :root{--bg:#0f1117;--panel:#171a23;--line:#262a36;--text:#e6e8ee;--muted:#9aa1b1;
       --ok:#34d399;--bad:#f87171}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--text);
      font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
 .wrap{max-width:860px;margin:0 auto;padding:56px 22px}
 h1{margin:0;font-size:30px;letter-spacing:-.02em}
 .sub{color:var(--muted);margin:8px 0 30px;font-size:14px}
 .banner{border-radius:12px;padding:14px 18px;margin-bottom:26px;font-weight:600;
         border:1px solid}
 .banner.ok{background:rgba(52,211,153,.10);border-color:rgba(52,211,153,.35);color:var(--ok)}
 .banner.bad{background:rgba(248,113,113,.10);border-color:rgba(248,113,113,.35);color:var(--bad)}
 table{width:100%;border-collapse:collapse;background:var(--panel);
       border:1px solid var(--line);border-radius:12px;overflow:hidden}
 th{text-align:left;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--muted);padding:12px 16px;border-bottom:1px solid var(--line);font-weight:600}
 td{padding:13px 16px;border-bottom:1px solid var(--line);vertical-align:top}
 tr:last-child td{border-bottom:none}
 .name{font-weight:600}
 .desc{color:var(--muted);font-size:13px}
 .pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:11px;
       letter-spacing:.08em;text-transform:uppercase;font-weight:700}
 .pill.up{background:rgba(52,211,153,.14);color:var(--ok)}
 .pill.down{background:rgba(248,113,113,.14);color:var(--bad)}
 code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:var(--muted)}
 footer{color:#6f7787;font-size:12.5px;margin-top:22px}
</style></head><body><div class="wrap">
<h1>Inception &middot; status</h1>
<p class="sub">Live probes of every container in the stack. Refreshes every 15 s.</p>
__BANNER__
<table>
<tr><th>Service</th><th>Target</th><th>State</th><th>Detail</th></tr>
__ROWS__
</table>
<footer>Generated at __NOW__ &middot; JSON at <code>/health</code></footer>
</div></body></html>
"""


def render(results):
    down = [r["service"] for r in results if not r["ok"]]
    if down:
        banner = '<div class="banner bad">%d service(s) not answering: %s</div>' % (
            len(down), escape(", ".join(down)))
    else:
        banner = '<div class="banner ok">All %d services are answering.</div>' % len(results)

    rows = []
    for r in results:
        rows.append(
            "<tr><td><div class='name'>%s</div><div class='desc'>%s</div></td>"
            "<td><code>%s</code></td>"
            "<td><span class='pill %s'>%s</span></td>"
            "<td><code>%s</code></td></tr>" % (
                escape(r["service"]), escape(r["description"]), escape(r["target"]),
                "up" if r["ok"] else "down", "up" if r["ok"] else "down",
                escape(r["detail"])))

    return (PAGE
            .replace("__BANNER__", banner)
            .replace("__ROWS__", "\n".join(rows))
            .replace("__NOW__", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())))


class Handler(BaseHTTPRequestHandler):
    server_version = "inception-status/1.0"

    def _send(self, code, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/health":
            results = collect()
            healthy = all(r["ok"] for r in results)
    
    
            self._send(200 if healthy else 503,
                       json.dumps({"healthy": healthy, "checks": results}, indent=2),
                       "application/json")
        elif path == "/":
            self._send(200, render(collect()), "text/html; charset=utf-8")
        else:
            self._send(404, "not found\n", "text/plain; charset=utf-8")

    def log_message(self, fmt, *args):
        print("[status] %s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print("[status] listening on 0.0.0.0:%d" % LISTEN_PORT)
    ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler).serve_forever()

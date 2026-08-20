"""A minimal HTTP health-check server.

Platforms like Koyeb require the container to listen on an HTTP port and
respond to health checks; otherwise the service is considered idle and may be
stopped. This tiny server (standard library only) keeps the service alive and
reportable without interfering with the bot's asyncio loop.
"""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from loguru import logger

HEALTH_PORT = 8080


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/health", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Silence the default per-request logging.
        return


def start_health_server(port: int = HEALTH_PORT) -> None:
    """Start the health server in a daemon thread."""
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    except OSError as exc:
        logger.warning("Health server could not bind to port {}: {}", port, exc)
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health server listening on 0.0.0.0:{}", port)

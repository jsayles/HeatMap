"""Local ASGI server for the desktop app, always bound to 127.0.0.1."""

import socket
import threading
import time

import uvicorn

HOST = '127.0.0.1'


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


class LocalServer:
    """Runs uvicorn in a background thread so the main thread can own the window."""

    def __init__(self, port, app='heatmap.asgi:application'):
        self.port = port
        self.config = uvicorn.Config(app, host=HOST, port=port, log_level='warning')
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    @property
    def url(self):
        return f'http://{HOST}:{self.port}'

    def start(self, timeout=10):
        self.thread.start()
        deadline = time.monotonic() + timeout
        while not self.server.started:
            if not self.thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError('Local server failed to start')
            time.sleep(0.02)

    def stop(self, timeout=10):
        self.server.should_exit = True
        self.thread.join(timeout)

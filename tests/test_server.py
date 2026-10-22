import socket

from heatmap.server import HOST, LocalServer, find_free_port


def _listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((HOST, port)) == 0


async def _app(scope, receive, send):
    # Minimal ASGI app so the test doesn't depend on Django.
    if scope['type'] == 'lifespan':
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})
                return


def test_find_free_port_returns_unused_port():
    port = find_free_port()
    assert 1024 < port < 65536
    assert not _listening(port)


def test_server_binds_to_loopback_only():
    server = LocalServer(find_free_port(), app=_app)
    assert server.config.host == '127.0.0.1'
    assert server.url.startswith('http://127.0.0.1:')


def test_server_starts_and_stops():
    port = find_free_port()
    server = LocalServer(port, app=_app)
    server.start()
    assert _listening(port)
    server.stop()
    assert not server.thread.is_alive()
    assert not _listening(port)

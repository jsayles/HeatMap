"""Desktop entry point: `uv run heatmap`.

Starts the local Django server in a background thread, opens it in a native
window, and shuts everything down when the window closes.
"""

import os
import secrets

# Functions called (in order) when the window closes, e.g. stopping recorders.
shutdown_hooks = []


def main():
    token = secrets.token_urlsafe(32)
    os.environ['HEATMAP_LAUNCH_TOKEN'] = token
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heatmap.settings')

    import django

    django.setup()

    from django.core.management import call_command

    call_command('migrate', verbosity=0)

    import webview

    from heatmap.server import LocalServer, find_free_port

    server = LocalServer(find_free_port())
    server.start()
    try:
        webview.create_window(
            'Personal Heat Map',
            f'{server.url}/launch/?token={token}',
            width=1280,
            height=820,
            min_size=(900, 600),
        )
        webview.start()
    finally:
        for hook in shutdown_hooks:
            hook()
        server.stop()


if __name__ == '__main__':
    main()

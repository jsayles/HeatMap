"""Per-launch secret so only the app's own window can talk to the local server.

heatmap.app generates a token at startup and opens the window on
/launch/?token=..., which stores it in a cookie. Every other request must
carry that cookie.
"""

import secrets

from asgiref.sync import iscoroutinefunction
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import sync_and_async_middleware

COOKIE_NAME = 'heatmap_launch'


def token_matches(value):
    expected = settings.LAUNCH_TOKEN
    return bool(expected) and bool(value) and secrets.compare_digest(value, expected)


def _is_exempt(path):
    return path == '/launch/' or path.startswith('/' + settings.STATIC_URL.lstrip('/'))


def _reject(request):
    if _is_exempt(request.path) or token_matches(request.COOKIES.get(COOKIE_NAME)):
        return None
    return HttpResponseForbidden('This app only accepts requests from its own window.')


@sync_and_async_middleware
def launch_token_middleware(get_response):
    if iscoroutinefunction(get_response):

        async def middleware(request):
            return _reject(request) or await get_response(request)

    else:

        def middleware(request):
            return _reject(request) or get_response(request)

    return middleware


def launch(request):
    token = request.GET.get('token', '')
    if not token_matches(token):
        return HttpResponseForbidden('Invalid launch token.')
    response = HttpResponseRedirect('/')
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite='Strict')
    return response

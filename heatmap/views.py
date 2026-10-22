from django.http import HttpResponse


def home(request):
    # Placeholder until the recording app provides the real home screen.
    return HttpResponse(
        '<!doctype html><title>Personal Heat Map</title>'
        '<body style="font-family: -apple-system, sans-serif; padding: 2rem">'
        '<h1>Personal Heat Map</h1><p>Session app is running.</p></body>'
    )

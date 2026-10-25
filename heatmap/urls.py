from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from heatmap.launch import launch

urlpatterns = [
    path('', include('body_map.urls')),
    path('launch/', launch, name='launch'),
    path('admin/', admin.site.urls),
]

# The app runs under uvicorn rather than runserver, so serve static and media files here.
# Media (subjects' photos) is behind the launch-secret middleware like every other URL.
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

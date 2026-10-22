from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from heatmap import views
from heatmap.launch import launch

urlpatterns = [
    path('', views.home, name='home'),
    path('launch/', launch, name='launch'),
    path('admin/', admin.site.urls),
]

# The app runs under uvicorn rather than runserver, so serve static files here.
urlpatterns += staticfiles_urlpatterns()

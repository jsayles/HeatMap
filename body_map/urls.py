from django.urls import path

from body_map import views

urlpatterns = [
    path('', views.home, name='home'),
    path('import/', views.import_portrait, name='import_portrait'),
]

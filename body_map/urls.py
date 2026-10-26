from django.urls import path

from body_map import views

urlpatterns = [
    path('', views.home, name='home'),
    path('import/', views.import_portrait, name='import_portrait'),
    path('portraits/<int:pk>/', views.portrait_detail, name='portrait_detail'),
    path('overlay/', views.overlay, name='overlay'),
]

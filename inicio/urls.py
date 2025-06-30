from django.urls import path, re_path
from .import views

app_name = 'inicio'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('upload-video/', views.upload_video, name='upload_video'),
    
]
from django.urls import path
from . import views
from .apps import AuditConfig
from .views import upload_file, upload_success

app_name = AuditConfig.name

urlpatterns = [
    path("", views.home, name="home"),
    path('upload/', upload_file, name='upload_file'),
    path('success/', upload_success, name='upload_success'),]

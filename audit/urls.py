from django.urls import path
from .apps import AuditConfig
from .views import home

app_name = AuditConfig.name

urlpatterns = [
    path("", home, name="home"),
]

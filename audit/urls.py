from django.urls import path
from . import views
from .apps import AuditConfig

app_name = AuditConfig.name

urlpatterns = [
    path('', views.home, name='home')
]

from django.urls import path
from .apps import AuditConfig
from .views import home, graph

app_name = AuditConfig.name

urlpatterns = [
    path("", home, name="home"),
    path("graph/", graph, name="graph"),
]

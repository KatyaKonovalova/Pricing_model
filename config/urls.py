from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('audit/', include('audit.urls', namespace='audit')),
    path('', RedirectView.as_view(url='/audit/', permanent=True)),
    path('users/', include('users.urls', namespace='users')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

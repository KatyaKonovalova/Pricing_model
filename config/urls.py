from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('audit/', include('audit.urls')),
    path('', RedirectView.as_view(url='/audit/', permanent=True)),
    path('user/', include('users.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

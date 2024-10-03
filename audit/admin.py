from django.contrib import admin
from .models import Audit


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("file", "user", "uploaded_date")
    search_fields = ("file", "user")
    list_filter = ("user", "uploaded_date")

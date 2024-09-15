from django.contrib import admin

from .models import Audit


# admin.site.register(Audit) - тоже самое, что и @admin.register(Audit)
@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('file', 'upload_date',)  # ToDo: добавить 'user'
    list_filter = ('upload_date',)
    search_fields = ('file', 'upload_date',)

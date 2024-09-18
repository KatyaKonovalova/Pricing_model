from django.contrib import admin

from .models import Audit
from .forms import AuditForm

@admin.register(Audit)
class Audit(admin.ModelAdmin):
    form = AuditForm  # Используем кастомную форму для админки

    # Отключаем остальные поля, если необходимо
    def save_model(self, request, obj, form, change):
        # Сохраняем только файл, не изменяя другие данные
        if form.is_valid():
            obj.file_field = form.cleaned_data['file']  # Сохраняем только файл
            obj.save()





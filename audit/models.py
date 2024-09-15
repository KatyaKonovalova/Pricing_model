from django.db import models

from users.models import User


class Audit(models.Model):
    file = models.FileField(
        upload_to="data/", verbose_name="csv-файл", help_text="Загрузите csv-файл"
    )
    upload_date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='Дата инженер', null=True, blank=True)

    # ToDo: добавить поле user

    class Meta:
        verbose_name = "Аудит"
        verbose_name_plural = "Аудиты"
        ordering = ["file", "upload_date"]

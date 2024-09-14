from django.db import models


class Audit(models.Model):
    file = models.FileField(
        upload_to="data/", verbose_name="csv-файл", help_text="Загрузите csv-файл"
    )
    # ToDo: кажется путь прописан неправильно
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Аудит"
        verbose_name_plural = "Аудиты"
        ordering = ["file", "upload_date"]
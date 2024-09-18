from django.db import models
from django.utils import timezone

from users.models import User


class Audit(models.Model):
    price = models.FloatField(verbose_name="Цена товара")
    count = models.PositiveIntegerField(verbose_name='Количество проданного товара')
    add_cost = models.FloatField(verbose_name='Затраты на производство')
    company = models.CharField(max_length=100, verbose_name='Компания')
    product = models.CharField(max_length=100, verbose_name='Товар')
    upload_date = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='data/', null=True, blank=True)

    class Meta:
        verbose_name = "Аудит"
        verbose_name_plural = "Аудиты"
        ordering = ['file', 'upload_date', 'uploaded_by']


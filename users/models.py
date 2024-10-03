from django.contrib.auth.models import AbstractUser
from django.db import models

from users.management.commands.csu import UserManager


class User(AbstractUser):
    PROFILE_VALUE_CHOICES = [("Analyst", "Аналитик"), ("Data engineer", "Дата инженер")]
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    profile_value = models.CharField(
        max_length=50,
        choices=PROFILE_VALUE_CHOICES,
        default="Analyst",
        verbose_name="Кем вы являетесь",
    )
    token = models.CharField(
        max_length=100, verbose_name="Token", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email

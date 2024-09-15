from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    PROFILE_VALUE_CHOICES = [('Аналитик', 'Analyst'), ('Дата инженер', 'Data engineer')]
    username = models.CharField()
    email = models.EmailField(unique=True, verbose_name="Email")
    profile_value = models.CharField(max_length=50,
                                     choices=PROFILE_VALUE_CHOICES,
                                     default="Аналитик",
                                     verbose_name="Кем вы являетесь",)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email

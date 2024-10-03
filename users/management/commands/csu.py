# from users.models import User
# from django.core.management import BaseCommand
#
#
# class Command(BaseCommand):
#     def handle(self, *args, **options):
#         user = User.objects.create(email="admin@example.com", first_name="Admin")
#         user.set_password("12345")
#         user.is_active = True
#         user.is_staff = True
#         user.is_superuser = True
#         user.save()

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Создает и возвращает пользователя с email и паролем."""
        if not email:
            raise ValueError("У пользователя должен быть email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает и возвращает суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

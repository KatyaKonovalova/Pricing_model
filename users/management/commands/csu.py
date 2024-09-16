from users.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(email="admin@example.com", first_name="Admin")
        user.set_password("12345")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

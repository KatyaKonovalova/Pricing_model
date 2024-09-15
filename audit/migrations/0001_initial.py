# Generated by Django 5.1.1 on 2024-09-15 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Audit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        help_text="Загрузите csv-файл",
                        upload_to="data/",
                        verbose_name="csv-файл",
                    ),
                ),
                ("upload_date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Аудит",
                "verbose_name_plural": "Аудиты",
                "ordering": ["file", "upload_date"],
            },
        ),
    ]

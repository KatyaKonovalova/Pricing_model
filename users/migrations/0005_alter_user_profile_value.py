# Generated by Django 5.1.1 on 2024-09-16 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_alter_user_profile_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="profile_value",
            field=models.CharField(
                choices=[("Analyst", "Аналитик"), ("Data engineer", "Дата инженер")],
                default="Аналитик",
                max_length=50,
                verbose_name="Кем вы являетесь",
            ),
        ),
    ]

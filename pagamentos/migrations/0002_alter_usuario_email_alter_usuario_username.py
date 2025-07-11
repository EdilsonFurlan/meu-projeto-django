# Generated by Django 5.2.3 on 2025-07-03 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pagamentos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="email",
            field=models.EmailField(
                max_length=254, unique=True, verbose_name="email address"
            ),
        ),
        migrations.AlterField(
            model_name="usuario",
            name="username",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]

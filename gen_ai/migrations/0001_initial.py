# Generated by Django 4.2.5 on 2023-10-05 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="params",
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
                ("collection_name", models.CharField(max_length=30)),
                ("ans_type", models.CharField(max_length=30)),
                ("inst_type", models.CharField(max_length=30)),
                ("inst", models.CharField(max_length=500)),
            ],
        ),
    ]

# Generated by Django 4.2.5 on 2023-10-05 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gen_ai", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="params",
            name="ans_type",
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name="params",
            name="inst",
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="params",
            name="inst_type",
            field=models.CharField(max_length=30, null=True),
        ),
    ]

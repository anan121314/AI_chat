# Generated by Django 4.2.5 on 2023-10-05 20:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gen_ai", "0002_alter_params_ans_type_alter_params_inst_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="params",
            name="inst_type",
        ),
    ]

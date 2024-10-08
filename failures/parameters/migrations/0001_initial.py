# Generated by Django 4.1.3 on 2022-12-07 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Parameter",
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
                    "value_type",
                    models.IntegerField(
                        choices=[
                            (1, "Integer"),
                            (2, "Float"),
                            (3, "String"),
                            (4, "Boolean"),
                        ],
                        verbose_name="Value Type",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, unique=True, verbose_name="Name"),
                ),
                (
                    "value",
                    models.CharField(
                        help_text='Type "True" or "False" for boolean values.',
                        max_length=255,
                        verbose_name="Value",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
            ],
            options={
                "verbose_name": "Parameter",
                "verbose_name_plural": "Parameters",
            },
        ),
    ]

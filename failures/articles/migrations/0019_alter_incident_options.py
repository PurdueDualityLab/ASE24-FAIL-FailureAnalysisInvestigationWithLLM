# Generated by Django 4.1.3 on 2023-05-03 21:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0018_alter_article_incident"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="incident",
            options={"verbose_name": "Incident", "verbose_name_plural": "Incident"},
        ),
    ]

# Generated by Django 4.1.3 on 2023-04-13 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0010_searchquery_end_month_searchquery_start_month"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="headline",
            field=models.TextField(blank=True, null=True, verbose_name="Headline"),
        ),
    ]

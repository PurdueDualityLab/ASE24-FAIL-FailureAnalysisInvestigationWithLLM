# Generated by Django 4.1.3 on 2023-04-12 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0006_failure_published"),
    ]

    operations = [
        migrations.AlterField(
            model_name="failure",
            name="application_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Application Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="behaviour_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Behaviour Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="boundary_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Boundary Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="capability_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Capability Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="communication_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Communication Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="cps_option",
            field=models.TextField(blank=True, null=True, verbose_name="CPS Option"),
        ),
        migrations.AlterField(
            model_name="failure",
            name="dimension_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Dimension Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="domain_option",
            field=models.TextField(blank=True, null=True, verbose_name="Domain Option"),
        ),
        migrations.AlterField(
            model_name="failure",
            name="duration_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Duration Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="intent_option",
            field=models.TextField(blank=True, null=True, verbose_name="Intent Option"),
        ),
        migrations.AlterField(
            model_name="failure",
            name="nature_option",
            field=models.TextField(blank=True, null=True, verbose_name="Nature Option"),
        ),
        migrations.AlterField(
            model_name="failure",
            name="objective_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Objective Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="perception_option",
            field=models.TextField(
                blank=True, null=True, verbose_name="Perception Option"
            ),
        ),
        migrations.AlterField(
            model_name="failure",
            name="phase_option",
            field=models.TextField(blank=True, null=True, verbose_name="Phase Option"),
        ),
    ]

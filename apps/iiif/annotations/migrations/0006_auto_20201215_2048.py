# Generated by Django 2.2.10 on 2020-12-15 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0005_annotation_style'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
    ]

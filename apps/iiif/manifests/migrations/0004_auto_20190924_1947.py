# Generated by Django 2.1.2 on 2019-09-24 19:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0003_auto_20190730_1852'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='manifest',
            options={'ordering': ['published_date']},
        ),
    ]

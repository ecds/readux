# Generated by Django 2.2.10 on 2021-01-08 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0012_auto_20200819_1608'),
    ]

    operations = [
        migrations.RenameField(
            model_name='manifest',
            old_name='viewingDirection',
            new_name='viewingdirection',
        ),
    ]

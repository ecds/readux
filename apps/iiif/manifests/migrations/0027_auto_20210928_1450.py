# Generated by Django 2.2.23 on 2021-09-28 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0026_auto_20210928_1447'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='pid',
            field=models.CharField(default='2qkkvj46', help_text="Unique ID. Do not use -'s or spaces in the pid.", max_length=255),
        ),
    ]
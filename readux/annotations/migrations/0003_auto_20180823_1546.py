# Generated by Django 2.1 on 2018-08-23 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0002_auto_20180823_1513'),
    ]

    operations = [
        migrations.RenameField(
            model_name='annotation',
            old_name='iif_annotation',
            new_name='iiif_annotation',
        ),
        migrations.AddField(
            model_name='annotation',
            name='uri',
            field=models.URLField(default='http://my.uri'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='annotation',
            name='volume_uri',
            field=models.URLField(blank=True),
        ),
    ]

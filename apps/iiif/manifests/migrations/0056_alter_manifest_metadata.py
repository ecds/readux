# Generated by Django 3.2.15 on 2023-09-25 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0055_alter_manifest_logo_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

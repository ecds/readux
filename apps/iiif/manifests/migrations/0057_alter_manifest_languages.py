# Generated by Django 3.2.15 on 2023-09-25 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0056_alter_manifest_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='languages',
            field=models.ManyToManyField(blank=True, help_text='Languages present in the manifest.', to='manifests.Language'),
        ),
    ]
# Generated by Django 2.2.10 on 2020-10-27 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canvases', '0005_auto_20201027_1452'),
    ]

    operations = [
        migrations.AddField(
            model_name='canvas',
            name='ocr_file_path',
            field=models.FilePathField(allow_folders=True, blank=True, null=True, path='/tmp', recursive=True),
        ),
        migrations.RemoveField(
            model_name='canvas',
            name='IIIF_IMAGE_SERVER_BASE',
        ),
        migrations.DeleteModel(
            name='IServer',
        ),
    ]

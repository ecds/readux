# Generated by Django 2.2.10 on 2021-01-07 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canvases', '0006_canvas_ocr_file_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='canvas',
            name='ocr_file_path',
            field=models.FilePathField(allow_folders=True, blank=True, null=True, path='/var/folders/6q/m6_cn6w96g158vldpfhnn6k40000gn/T', recursive=True),
        ),
    ]

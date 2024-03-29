# Generated by Django 3.2.13 on 2022-06-07 14:53

from datetime import datetime
import apps.utils.noid
from django.db import migrations, models

def add_dates(apps, _):
    Canvas = apps.get_model("canvases", "Canvas")  # pylint: disable=invalid-name
    for canvas in Canvas.objects.all():
        canvas.created_at = canvas.manifest.created_at
        canvas.updated_at = canvas.manifest.updated_at


class Migration(migrations.Migration):

    dependencies = [
        ('canvases', '0026_alter_canvas_pid'),
    ]

    operations = [
        migrations.AddField(
            model_name='canvas',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='canvas',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='canvas',
            name='label',
            field=models.CharField(default='', max_length=1000),
        ),
        migrations.RunPython(add_dates, migrations.RunPython.noop),
]

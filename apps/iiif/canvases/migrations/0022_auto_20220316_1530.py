# Generated by Django 2.2.24 on 2022-03-16 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canvases', '0021_auto_20220316_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='canvas',
            name='pid',
            field=models.CharField(default='2r7vqn48', help_text="Unique ID. Do not use _'s or spaces in the pid.", max_length=255),
        ),
    ]
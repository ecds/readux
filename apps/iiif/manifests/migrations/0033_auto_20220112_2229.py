# Generated by Django 2.2.24 on 2022-01-12 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0032_auto_20211028_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='pid',
            field=models.CharField(default='2qt0qzj8', help_text="Unique ID. Do not use _'s or spaces in the pid.", max_length=255),
        ),
    ]

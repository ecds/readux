# Generated by Django 2.2.10 on 2021-06-18 16:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0009_delete_annotationgroup'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='annotation',
            options={'ordering': ['order']},
        ),
    ]

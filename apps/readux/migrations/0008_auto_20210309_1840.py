# Generated by Django 2.2.10 on 2021-03-09 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readux', '0007_auto_20201215_2048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userannotation',
            name='content',
            field=models.TextField(blank=True, default=' ', null=True),
        ),
    ]

# Generated by Django 2.2.10 on 2020-04-07 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kollections', '0004_auto_20190415_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

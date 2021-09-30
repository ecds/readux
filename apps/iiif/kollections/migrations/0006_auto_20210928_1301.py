# Generated by Django 2.2.23 on 2021-09-28 13:01

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('kollections', '0005_collection_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='collection',
            name='label',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='collection',
            name='label_de',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='label_en',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='collection',
            name='pid',
            field=models.CharField(default='2qkkkqds', help_text="Unique ID. Do not use -'s or spaces in the pid.", max_length=255),
        ),
    ]
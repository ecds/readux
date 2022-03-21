# Generated by Django 2.2.24 on 2022-03-16 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0038_auto_20220316_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='manifest',
            name='identifier',
            field=models.CharField(blank=True, help_text='Call number or other unique id.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='manifest',
            name='identifier_uri',
            field=models.URLField(blank=True, help_text='Only enter a link to a catalog record.', null=True),
        ),
        migrations.AddField(
            model_name='manifest',
            name='language',
            field=models.CharField(blank=True, help_text='Enter multiple entities separated by a semicolon (;).', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='manifest',
            name='scanned_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='manifest',
            name='pid',
            field=models.CharField(default='2r7vqn48', help_text="Unique ID. Do not use _'s or spaces in the pid.", max_length=255),
        ),
    ]
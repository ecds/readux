# Generated by Django 3.2.15 on 2023-09-25 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0036_alter_s3ingest_metadata_spreadsheet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='local',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='remote',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='s3ingest',
            name='s3_bucket',
            field=models.CharField(help_text="The name of a publicly-accessible S3 bucket containing volumes to\n        ingest, either at the bucket root or within subfolder(s). Each volume should have its own\n        subfolder, with the volume's PID as its name.\n        <br />\n        <strong>Example:</strong> if the bucket's URL is\n        https://my-bucket.s3.us-east-1.amazonaws.com/, its name is <strong>my-bucket</strong>.", max_length=255),
        ),
    ]
